"""Persistent sequential batches and bounded-memory ZIP exports; no model changes."""
import asyncio
import hashlib
import json
import re
import shutil
import uuid
import zipfile
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from .worker import write

MAX_FILES = 20
MAX_INPUT_BYTES = 2 * 1024**3


def recover_batches(root):
    for path in (root / 'batches').glob('*/batch.json'):
        try:
            state = json.loads(path.read_text())
            if state['status'] == 'running':
                state.update(status='interrupted', error='服务重启，已完成的结果已保留；可继续未完成文件。')
                write(path, state)
        except (OSError, ValueError, KeyError):
            pass


def safe_name(value):
    return re.sub(r'[\x00-\x1f/\\:*?"<>|]', '_', value).strip(' .')[:120] or '音频'


def install_batch_routes(app, data, validate, store_input, load_job, public_job, execute, claim, release, reuse_input=None):
    root = data.parent
    batches = root / 'batches'
    exports = root / 'exports'
    batches.mkdir(exist_ok=True)
    exports.mkdir(exist_ok=True)
    upload_lock = asyncio.Lock()
    export_lock = asyncio.Lock()

    def load(batch_id):
        if not re.fullmatch(r'[a-f0-9]{32}', batch_id):
            raise HTTPException(404, '批次不存在。')
        path = batches / batch_id / 'batch.json'
        if not path.exists():
            raise HTTPException(404, '批次不存在。')
        return path, json.loads(path.read_text())

    def describe(state):
        jobs = [public_job(item) for item in state['jobs']]
        return state | {'jobs': jobs, 'completed': sum(j['status'] == 'succeeded' for j in jobs)}

    async def run(path):
        try:
            state = json.loads(path.read_text())
            for job_id in state['jobs']:
                job_path = data / job_id / 'job.json'
                job = load_job(job_id)
                if job['status'] == 'succeeded':
                    continue
                job.update(status='queued', error='', outputs=[])
                write(job_path, job)
                try:
                    await execute(job_path, release_slot=False)
                except Exception:
                    job = load_job(job_id)
                    job.update(status='failed', error='处理未完成，可继续本批次重试。', outputs=[])
                    write(job_path, job)
            failed = any(load_job(item)['status'] != 'succeeded' for item in state['jobs'])
            state.update(status='partial' if failed else 'succeeded', error='部分文件未完成，可继续重试。' if failed else '')
            write(path, state)
        finally:
            release()

    @app.post('/api/studio/batches', status_code=201)
    def create(model: str, stems: str, purpose: str = 'duo'):
        selected = validate(model, stems)
        batch_id = uuid.uuid4().hex
        folder = batches / batch_id
        folder.mkdir()
        state = dict(id=batch_id, model=model, stems=selected, purpose=purpose, status='preparing', jobs=[], bytes=0, uploaded_bytes=0, reused_files=0)
        write(folder / 'batch.json', state)
        return describe(state)

    @app.post('/api/studio/batches/{batch_id}/inputs', status_code=201)
    async def add(batch_id: str, request: Request, filename: str):
        async with upload_lock:
            path, state = load(batch_id)
            if state['status'] != 'preparing':
                raise HTTPException(409, '该批次已开始，请新建批次添加音频。')
            if len(state['jobs']) >= MAX_FILES:
                raise HTTPException(400, '每批最多20个文件。')
            remaining = MAX_INPUT_BYTES - state['bytes']
            if int(request.headers.get('content-length', '0')) > remaining:
                raise HTTPException(413, '每批音频合计不能超过2 GB。')
            # Bound even chunked requests without buffering whole files in memory.
            class LimitedInput:
                async def stream(self):
                    size = 0
                    async for chunk in request.stream():
                        size += len(chunk)
                        if size > remaining:
                            raise HTTPException(413, '每批音频合计不能超过2 GB。')
                        yield chunk
            job_id = await store_input(LimitedInput(), state['model'], filename, json.dumps(state['stems']), state['purpose'])
            state['jobs'].append(job_id)
            state['bytes'] += (data / job_id / 'input.audio').stat().st_size
            state['uploaded_bytes'] = state.get('uploaded_bytes', 0) + (data / job_id / 'input.audio').stat().st_size
            write(path, state)
            return describe(state)

    @app.post('/api/studio/batches/{batch_id}/start', status_code=202)
    async def start(batch_id: str):
        async with upload_lock:
            path, state = load(batch_id)
            if state['status'] in {'running', 'succeeded'}:
                return describe(state)  # Repeated starts never repeat successful inference.
            if not state['jobs']:
                raise HTTPException(400, '请先上传音频。')
            validate(state['model'], json.dumps(state['stems']))
            claim()
            try:
                state.update(status='running', error='')
                write(path, state)
                asyncio.create_task(run(path))
            except BaseException:
                release()
                raise
            return describe(state)

    @app.post('/api/studio/batches/{batch_id}/reuse', status_code=201)
    async def reuse(batch_id: str, asset_id: str):
        async with upload_lock:
            path, state = load(batch_id)
            if state['status'] != 'preparing':
                raise HTTPException(409, '该批次已开始，请新建批次。')
            if len(state['jobs']) >= MAX_FILES:
                raise HTTPException(400, '每批最多20个文件。')
            if reuse_input is None:
                raise HTTPException(503, '音频复用暂不可用。')
            source = public_job(asset_id)
            size = source.get('input_bytes', 0)
            if not source.get('input_asset_id'):
                raise HTTPException(404, '已上传音频不存在，请重新选择文件。')
            if size + state['bytes'] > MAX_INPUT_BYTES:
                raise HTTPException(413, '每批音频合计不能超过2 GB。')
            job_id = reuse_input(asset_id, state['model'], state['stems'], state['purpose'])
            state['jobs'].append(job_id)
            state['bytes'] += size
            state['reused_files'] = state.get('reused_files', 0) + 1
            write(path, state)
            return describe(state)

    @app.get('/api/studio/batches/{batch_id}')
    def read(batch_id: str):
        return describe(load(batch_id)[1])

    def pack(tracks):
        if not isinstance(tracks, list) or not 1 <= len(tracks) <= 400:
            raise HTTPException(400, '请选择1至400条已完成的音轨。')
        entries, identity, seen = [], [], set()
        for item in tracks:
            if not isinstance(item, dict):
                raise HTTPException(400, '音轨选择无效。')
            job_id, stem = item.get('job_id', ''), item.get('stem', '')
            if not isinstance(job_id, str) or not isinstance(stem, str):
                raise HTTPException(400, '音轨选择无效。')
            if (job_id, stem) in seen:
                continue
            seen.add((job_id, stem))
            job = load_job(job_id)
            output = next((o for o in job['outputs'] if o['stem'] == stem), None)
            if job['status'] != 'succeeded' or not output:
                raise HTTPException(409, '所选音轨尚未完成。')
            path = data / job_id / output['file']
            stat = path.stat()
            label = next(o['label'] for o in public_job(job_id)['outputs'] if o['stem'] == stem)
            entries.append((job_id, path, safe_name(Path(job['filename']).stem), safe_name(label)))
            identity.append([job_id, stem, stat.st_size, stat.st_mtime_ns])
        export_id = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
        target = exports / (export_id + '.zip')
        if not target.exists():
            size = sum(row[2] for row in identity)
            if shutil.disk_usage(exports).free < size + 256 * 1024**2:
                raise HTTPException(507, '导出空间不足，请减少所选音轨。')
            names = list(dict.fromkeys(e[0] for e in entries))
            temporary = target.with_suffix('.tmp')
            try:
                with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
                    for index, (job_id, path, filename, label) in enumerate(entries, 1):
                        archive.write(path, f'{names.index(job_id)+1:02d}-{filename}/{index:03d}-{label}.wav')
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        return dict(url=f'/api/studio/exports/{export_id}.zip', filename='分离音轨.zip', bytes=target.stat().st_size, tracks=len(entries))

    @app.post('/api/studio/exports', status_code=201)
    async def export(request: Request):
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 65536:
                raise HTTPException(413, '所选音轨过多。')
        try:
            payload = json.loads(body)
            tracks = payload['tracks']
        except (ValueError, KeyError, TypeError):
            raise HTTPException(400, '请选择需要导出的音轨。')
        async with export_lock:
            return await asyncio.to_thread(pack, tracks)

    @app.get('/api/studio/exports/{export_id}.zip')
    def download(export_id: str):
        if not re.fullmatch(r'[a-f0-9]{64}', export_id):
            raise HTTPException(404, '导出文件不存在。')
        path = exports / (export_id + '.zip')
        if not path.exists():
            raise HTTPException(404, '导出文件不存在。')
        return FileResponse(path, media_type='application/zip', filename='分离音轨.zip')
