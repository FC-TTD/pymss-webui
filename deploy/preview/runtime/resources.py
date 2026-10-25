"""Wait for native GPU capacity; retry transient OOM without altering inference."""
import asyncio
import json
import math
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from .worker import write

MIB = 1024**2


async def free_memory():
    # CDI can rewrite NVIDIA_VISIBLE_DEVICES to "void" for PID 1, while docker
    # exec shows the configured value. Use the pinned application assignment.
    device = os.environ.get('STUDIO_GPU_UUID', '').strip()
    if not device:
        device = os.environ.get('NVIDIA_VISIBLE_DEVICES', '').split(',')[0]
        if not (device.startswith('GPU-') or device.isdigit()):
            device = os.environ.get('CUDA_VISIBLE_DEVICES', '0').split(',')[0]
    def query():
        result = subprocess.run(
            ['nvidia-smi', '-i', device, '--query-gpu=memory.free', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=4, check=True)
        return int(result.stdout.strip().splitlines()[0])
    try:
        return await asyncio.to_thread(query)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def required_memory(model_id, root):
    peak = 0
    for path in [root / 'smoke' / model_id / 'job.json', root / 'gpu-requirements.json']:
        try:
            state = json.loads(path.read_text())
            value = state.get(model_id, 0) if path.name == 'gpu-requirements.json' else state.get('peak_cuda_bytes', 0)
            peak = max(peak, int(value))
        except (OSError, ValueError, TypeError):
            pass
    # PyTorch's allocated peak excludes the CUDA context and part of its reserve.
    return math.ceil(peak / MIB) + 512 if peak else 3072


def remember_peak(model_id, peak, root):
    if not peak:
        return
    path = root / 'gpu-requirements.json'
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError):
        state = {}
    state[model_id] = max(int(peak), state.get(model_id, 0))
    write(path, state)


def is_oom(state):
    error = state.get('error', '').lower()
    return state.get('status') == 'failed' and ('cuda out of memory' in error or 'cuda error: out of memory' in error)


async def run_worker(path, log_path):
    with log_path.open('w') as log:
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'studio_runtime.worker', str(path), stdout=log, stderr=log)
        return await process.wait()


async def execute_with_capacity(path, probe=free_memory, launch=run_worker, wait_seconds=600, interval=2, attempts=3):
    path = Path(path)
    root = path.parent.parent.parent
    state = json.loads(path.read_text())
    required = required_memory(state['model'], root)
    deadline = time.monotonic() + wait_seconds
    session = uuid.uuid4().hex[:8]
    for attempt in range(1, attempts + 1):
        while True:
            free = await probe()
            if free is not None and free >= required:
                break
            state = json.loads(path.read_text())
            if time.monotonic() >= deadline:
                state.update(status='failed', error='等待显卡资源超过10分钟，音频已保留，可继续未完成文件。', error_code='gpu_capacity_timeout', outputs=[])
                write(path, state)
                return
            state.update(status='waiting', error='', message='显卡正被其他任务使用，已排队等待，音频无需重新上传。' if free is not None else '暂时无法读取显卡状态，正在等待恢复，音频已保留。',
                         retry_count=attempt - 1, required_gpu_mb=required, free_gpu_mb=free)
            write(path, state)
            await asyncio.sleep(interval)
        state = json.loads(path.read_text())
        log_path = path.with_name(f'job-attempt-{session}-{attempt}.log')
        state.update(status='queued', error='', error_code='', message='正在启动分离…', retry_count=attempt - 1,
                     required_gpu_mb=required, free_gpu_mb=free, attempt_log=log_path.name)
        write(path, state)
        code = await launch(path, log_path)
        state = json.loads(path.read_text())
        if state.get('status') == 'succeeded' and not code:
            remember_peak(state['model'], state.get('peak_cuda_bytes', 0), root)
            return
        if not is_oom(state):
            if code or state.get('status') != 'failed':
                state.update(status='failed', error='模型运行中断，音频已保留，可继续未完成文件。', outputs=[])
                write(path, state)
            return
        # The worker has exited, so its CUDA allocations have already been released.
        if attempt == attempts:
            state.update(error='此模型当前显存不足，已自动重试2次。音频已保留，可继续未完成文件。', error_code='gpu_capacity_exhausted')
            write(path, state)
            return
        state.update(status='waiting', error='', message=f'显卡资源发生抢占，正在等待并自动重试（{attempt}/{attempts-1}），音频已保留。', retry_count=attempt)
        write(path, state)
        await asyncio.sleep(interval)
