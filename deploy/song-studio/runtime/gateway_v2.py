"""Opt-in Stage consumer for pinned Gateway v2 separation profiles."""
import hashlib
import json
import os
import time
from pathlib import Path

import requests
import soundfile as sf

from .native_worker import label, write

VERSION='2026-10-28.v2'
PROFILES={
    'melband_roformer_instvox_duality_v2.ckpt':('dialogue-vocal',{'vocals':'Vocals','instrumental':'Instrumental'}),
    'bs_roformer_karaoke_anvuew.ckpt':('karaoke-anvuew',{'vocals':'Vocals','backing':'Instrumental'}),
    'mel_band_roformer_karaoke_becruily.ckpt':('karaoke-becruily',{'vocals':'Vocals','backing':'Instrumental'}),
    'becruily_deux.ckpt':('film-dialogue-deux',{'dialogue':'Vocals','background':'Instrumental'}),
    'model_bandit_plus_dnr_sdr_11.47.ckpt':('fx',{'dialogue':'Speech','music':'Music','fx':'Effects'}),
}

def enabled(model):
    return os.getenv('STUDIO_GATEWAY_V2_SEPARATION')=='1' and model in PROFILES

def _payload(response, expected):
    if response.status_code not in (expected if isinstance(expected,tuple) else (expected,)):
        raise RuntimeError(f'Gateway v2 HTTP {response.status_code}')
    return response.json()

def _download(http,base,task_id,artifact,target,expected_frames,channels):
    url=f'{base}/v2/audio/separations/{task_id}/artifacts/{artifact["id"]}'
    temporary=target.with_suffix('.gateway.tmp')
    digest=hashlib.sha256();size=0
    try:
        with http.get(url,stream=True,timeout=(10,60),allow_redirects=False) as response:
            if response.status_code!=200:raise RuntimeError(f'Gateway artifact HTTP {response.status_code}')
            with temporary.open('wb') as output:
                for block in response.iter_content(1024*1024):
                    if block:output.write(block);digest.update(block);size+=len(block)
        if size!=artifact['size_bytes'] or digest.hexdigest()!=artifact['sha256']:
            raise ValueError('Gateway 音轨哈希或大小不一致')
        info=sf.info(temporary)
        if info.samplerate!=48000 or info.channels!=channels or info.subtype!='PCM_24' or abs(info.frames-expected_frames)>1:
            raise ValueError('Gateway 音轨采样率、声道、精度或长度不一致')
        os.replace(temporary,target)
        return info.frames
    finally:
        temporary.unlink(missing_ok=True)

def run(path):
    path=Path(path);job=json.loads(path.read_text());started=time.time()
    profile,roles=PROFILES[job['model']]
    if not set(job['stems']).issubset(roles.values()):
        job.update(status='failed',error='所选音轨与 Gateway Profile 不一致');write(path,job);return
    asset=job.get('input_asset_id')
    if not isinstance(asset,str) or len(asset)!=32 or any(c not in '0123456789abcdef' for c in asset):
        job.update(status='failed',error='缺少 canonical asset ID');write(path,job);return
    index=job.get('segment_index')
    if index is not None and (not isinstance(index,int) or index<0):
        job.update(status='failed',error='分段编号无效');write(path,job);return
    expected_key=f'stage-{job["id"]}-{index if index is not None else "whole"}'
    key=job.get('gatewayV2Key') or expected_key
    if key!=expected_key:
        job.update(status='unknown',error='Gateway 提交键不一致，停止执行');write(path,job);return
    job.update(managedV2=True,gatewayV2Key=key,status='running',message='正在等待受管分轨任务');write(path,job)
    http=requests.Session();http.trust_env=False
    base=os.getenv('STUDIO_GATEWAY_V2_URL','http://model-gateway').rstrip('/')
    try:
        http.headers['Authorization']='Bearer '+Path(os.environ['NATIVE_GATEWAY_KEY_FILE']).read_text().strip()
        if not job.get('gatewayV2Task'):
            imported=_payload(http.post(base+'/v2/audio/separations/inputs/stage',json={'asset_id':asset,**({'segment':index} if index is not None else {})},timeout=(10,120),allow_redirects=False),(200,201))
            # Repeated canonical imports return 200 with the same authority record.
            input_row={name:imported[name] for name in ('id','file_ref','input_hash')}
            body={'profile_id':profile,'profile_version':VERSION,'inputs':[input_row],
                  'options':{'audio_params':{'channels':'source','sample_rate':48000,'wav_bit_depth':'PCM_24'}}}
            response=http.post(base+'/v2/audio/separations',json=body,headers={'Idempotency-Key':key},timeout=(10,120),allow_redirects=False)
            task=_payload(response,202)
            if task.get('profile_id')!=profile or task.get('profile_version')!=VERSION or not task.get('id'):
                raise ValueError('Gateway 返回的任务身份不一致')
            job['gatewayV2Task']=task['id'];write(path,job)
        task_id=job['gatewayV2Task']
        deadline=time.monotonic()+4*3600
        while True:
            task=_payload(http.get(f'{base}/v2/audio/separations/{task_id}',timeout=(10,60),allow_redirects=False),200)
            if task.get('id')!=task_id or task.get('profile_id')!=profile or task.get('profile_version')!=VERSION:
                raise ValueError('Gateway 任务身份不一致')
            state=task.get('state')
            if state in ('succeeded','failed','cancelled','unknown'):break
            if time.monotonic()>deadline:raise TimeoutError('Gateway 任务仍在运行，保留任务号待恢复')
            job.update(status='waiting' if state=='queued' else 'running',message='Gateway 任务排队中' if state=='queued' else 'Gateway 正在分离音轨');write(path,job)
            time.sleep(2)
        if state!='succeeded':
            job.update(status='unknown' if state=='unknown' else 'failed',error=task.get('error') or f'Gateway 任务状态：{state}');write(path,job);return
        inputs=task.get('inputs') or []
        if len(inputs)!=1 or inputs[0].get('state')!='succeeded':raise ValueError('Gateway 输入结果不完整')
        artifacts={item['role']:item for item in inputs[0].get('artifacts',[])}
        if set(artifacts)!=set(roles):raise ValueError('Gateway 分轨角色不完整')
        info=sf.info(job['input']);expected=round(info.frames/info.samplerate*48000)
        outputs=[]
        for role,stem in roles.items():
            if stem not in job['stems']:continue
            artifact=artifacts[role]
            if artifact.get('sample_rate')!=48000 or artifact.get('bits_per_sample')!=24:
                raise ValueError('Gateway 分轨媒体合同不一致')
            name=hashlib.sha256(stem.encode()).hexdigest()[:16]+'.wav'
            frames=_download(http,base,task_id,artifact,path.parent/name,expected,info.channels)
            outputs.append(dict(stem=stem,label=label(stem),file=name,frames=frames,channels=info.channels,sample_rate=48000))
        job.update(status='succeeded',outputs=outputs,error='',message='分离完成',seconds=round(time.time()-started,2),managedProvider='pymss-v2')
    except (requests.RequestException,TimeoutError) as exc:
        job.update(status='unknown',error=f'Gateway 通信中断，原提交键和任务号已保留：{type(exc).__name__}')
    except Exception as exc:
        job.update(status='unknown' if job.get('gatewayV2Task') else 'failed',error=str(exc))
    finally:
        http.close();write(path,job)
