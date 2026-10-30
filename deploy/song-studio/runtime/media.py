"""Disk streamed film ingest. Originals immutable; selected audio cached per stream."""
import asyncio, hashlib, json, math, shutil, uuid
from pathlib import Path
from fastapi import HTTPException, Request

MAX_FILE = 16 * 1024**3
MAX_BATCH = 64 * 1024**3

async def command(*args):
    proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await proc.communicate()
    except BaseException:
        if proc.returncode is None: proc.kill()
        await proc.wait()
        raise
    if proc.returncode:
        raise HTTPException(400, '无法读取媒体音轨，请检查文件是否完整或加密。')
    return stdout

async def probe(path):
    raw = await command('ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path))
    data = json.loads(raw)
    streams=[]
    for stream in data.get('streams',[]):
        if stream.get('codec_type') != 'audio': continue
        tags=stream.get('tags',{})
        duration=float(stream.get('duration') or data.get('format',{}).get('duration') or 0)
        if not math.isfinite(duration) or duration<=0: continue
        streams.append(dict(index=stream['index'], language=tags.get('language','未标注语言'),
            title=tags.get('title','音轨 '+str(len(streams)+1)), channels=stream.get('channels',0),
            channel_layout=stream.get('channel_layout',''), sample_rate=int(stream.get('sample_rate',0)),duration=duration))
    if not streams: raise HTTPException(400,'这个文件没有可读取的音频轨道。')
    return streams

async def receive(request, target):
    size=0; digest=hashlib.sha256()
    if shutil.disk_usage(target.parent).free < 2*1024**3:
        raise HTTPException(507,'存储空间不足，原文件未开始上传。')
    with target.open('xb') as file:
        async for chunk in request.stream():
            size+=len(chunk)
            if size>MAX_FILE: raise HTTPException(413,'单个文件最多16 GB。')
            if size%(64*1024**2)<len(chunk) and shutil.disk_usage(target.parent).free<2*1024**3: raise HTTPException(507,'存储空间不足，上传未完成。')
            digest.update(chunk);file.write(chunk)
    if not size: raise HTTPException(400,'文件为空。')
    return size,digest.hexdigest()

def downmix(stream):
    layout=stream.get('channel_layout','')
    channels=stream.get('channels',0)
    if channels<=2:return []
    # Explicit normalized fold-down: center, surrounds and LFE all contribute.
    names={
      '3.0':['FL','FR','FC'], 'quad':['FL','FR','BL','BR'],
      '4.0':['FL','FR','FC','BC'], '5.0':['FL','FR','FC','BL','BR'],
      '5.0(side)':['FL','FR','FC','SL','SR'],
      '5.1':['FL','FR','FC','LFE','BL','BR'],
      '5.1(side)':['FL','FR','FC','LFE','SL','SR'],
      '7.1':['FL','FR','FC','LFE','BL','BR','SL','SR'],
    }.get(layout)
    if names is None:raise HTTPException(400,'暂不支持这个多声道布局，请先转为标准5.1、7.1或立体声。')
    def side(main,others):
        terms=[main]+['0.707*'+n for n in others if n in names]+(['0.5*LFE'] if 'LFE' in names else [])
        return '+'.join(terms)
    return ['-af','pan=stereo|FL<'+side('FL',['FC','BL','SL','BC'])+'|FR<'+side('FR',['FC','BR','SR','BC'])]

async def extract(source,target,index):
    # FFmpeg's layout-aware stereo downmix includes center and surround channels.
    # No video decode, browser PCM buffer, normalization or sample-rate conversion.
    stream=next(s for s in await probe(source) if s['index']==index)
    required=int(stream['duration']*max(stream['sample_rate'],48000)*2*3)+2*1024**3
    if shutil.disk_usage(target.parent).free<required:raise HTTPException(507,'存储空间不足，未开始提取音轨。')
    await command('ffmpeg','-nostdin','-v','error','-i',str(source),'-map','0:'+str(index),
        '-vn','-sn','-dn',*downmix(stream),'-ac','2','-c:a','flac','-compression_level','1','-f','flac',str(target))
    import soundfile as sf
    info=sf.info(target)
    if info.channels!=2 or info.frames<=0: raise HTTPException(400,'音轨提取未完成。')
    return info

def install_media(app,data,write):
    root=data.parent/'media';root.mkdir(exist_ok=True)
    lock=asyncio.Lock()
    def load(identity):
        if len(identity)!=32 or any(c not in '0123456789abcdef' for c in identity):raise HTTPException(404)
        path=root/identity/'media.json'
        if not path.is_file():raise HTTPException(404)
        return path,json.loads(path.read_text())
    @app.post('/api/studio/media',status_code=201)
    async def upload(request:Request,filename:str):
        identity=uuid.uuid4().hex;folder=root/identity;folder.mkdir()
        size,digest=await receive(request,folder/'original.media')
        streams=await probe(folder/'original.media')
        state=dict(id=identity,filename=Path(filename).name,bytes=size,sha256=digest,streams=streams,assets={})
        write(folder/'media.json',state)
        return {k:v for k,v in state.items() if k!='assets'}
    @app.post('/api/studio/media/{identity}/prepare',status_code=201)
    async def prepare(identity:str,index:int):
        async with lock:
            path,state=load(identity)
            stream=next((s for s in state['streams'] if s['index']==index),None)
            if stream is None: raise HTTPException(400,'音轨不存在。')
            asset=state['assets'].get(str(index))
            if not asset:
                asset=uuid.uuid4().hex;folder=data/asset;folder.mkdir()
                info=await extract(path.parent/'original.media',folder/'input.audio',index)
                if abs(info.duration-stream['duration'])>max(2,stream['duration']*.001):
                    raise HTTPException(400,'提取时长与来源不一致，未提交分离。')
                write(folder/'job.json',dict(id=asset,model='',filename=state['filename'],purpose='input',
                    input=str(folder/'input.audio'),input_asset_id=asset,input_bytes=state['bytes'],
                    input_duration=info.duration,input_sha256=state['sha256'],stems=[],status='input',outputs=[],
                    source_media=identity,source_stream=index))
                state['assets'][str(index)]=asset;write(path,state)
            job=json.loads((data/asset/'job.json').read_text())
            return dict(asset_id=asset,duration=job['input_duration'],bytes=state['bytes'],filename=state['filename'],input_url='/api/studio/assets/'+asset+'/audio')
