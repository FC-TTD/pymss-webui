"""Existing PYMSS native protocol, exact song model and parameter identities."""
import hashlib
import io
import json
import os
import time
from pathlib import Path
from uuid import uuid4
import zipfile
import numpy as np
import requests
import soundfile as sf
from .native_worker import write, resample, label

SONG_MODELS={'melband_roformer_instvox_duality_v2.ckpt','bs_roformer_karaoke_anvuew.ckpt','mel_band_roformer_karaoke_becruily.ckpt'}
ORIGIN='http://model-gateway/internal/native/music-separation'


def run_song(path):
 path=Path(path);job=json.loads(path.read_text());started=time.time();submitted=False
 if job.get('managedAttempt'):
  job.update(status='unknown',error='已有受管执行记录，请先核对，未重复提交');write(path,job);return
 job.update(managedSong=True,managedAttempt=uuid4().hex,status='running',message='等待分离模型资源');write(path,job)
 http=requests.Session();http.trust_env=False
 # The CPU facade obtains queue/load/reclaim through the internal producer.
 # This file is mounted server-side; no client browser receives the key.
 http.headers['Authorization']='Bearer '+Path(os.environ['NATIVE_GATEWAY_KEY_FILE']).read_text().strip()
 try:
  assert job['model'] in SONG_MODELS
  manifest=json.loads(Path('/model-cache/download-manifest.json').read_text())
  model=next(m for m in manifest['models'] if m['id']==job['model'])
  # The same native CPU decoder and original config determine input rate.
  from pymss.config import load_config
  from pymss.audio_io import load_audio
  config=load_config(model['artifacts'][1]['path']);sr=int(config.audio.get('sample_rate',44100))
  mix,_=load_audio(job['input'],sr=sr,mono=False);mix=np.asarray(mix,dtype='float32')
  if mix.ndim==1:mix=mix[None,:]
  assert mix.shape[0] in [1,2] and np.isfinite(mix).all()
  load_id=uuid4().hex;job['managedLoadRequest']=load_id;write(path,job)
  loaded=http.post(ORIGIN+'/v1/models/load',json={'model':job['model'],'inference_params':{'batch_size':1}},headers={'X-Request-ID':load_id},timeout=(10,720),allow_redirects=False)
  if loaded.status_code!=200:raise RuntimeError('受管模型加载未完成（HTTP '+str(loaded.status_code)+'），未提交分离')
  job.update(message='正在分离音轨',managedInferenceRequest=uuid4().hex);write(path,job)
  # Native model identity is mandatory. A concurrent UI switch fails closed
  # under the provider's shared gate; it cannot silently use another model.
  params=dict(model=job['model'],format='pcm_f32le',sample_rate=sr,channels=mix.shape[0],stems=','.join(job['stems']),response_format='zip',output_audio_format='pcm_f32le')
  submitted=True
  response=http.post(ORIGIN+'/v1/audio/separations',params=params,data=np.ascontiguousarray(mix.T,dtype='<f4').tobytes(),headers={'Content-Type':'application/octet-stream','X-Request-ID':job['managedInferenceRequest']},timeout=(10,1800),allow_redirects=False)
  if response.status_code!=200:
   # Resource uncertainty must not become a retryable native failure.
   job.update(status='unknown' if response.status_code in [502,503,504] else 'failed',error='受管分离未完成（HTTP '+str(response.status_code)+'），原执行记录保留，未自动重跑');write(path,job);return
  outputs=[]
  with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
   metadata=json.loads(archive.read('manifest.json'))
   if metadata['model']!=job['model']:raise ValueError('模型身份不一致')
   for row in metadata['outputs']:
    if row['stem'] not in job['stems'] or row['format']!='pcm_f32le' or row['sample_rate']!=sr:raise ValueError('原生输出合同不一致')
    raw=archive.read(row['filename']);channels=int(row['channels']);audio=np.frombuffer(raw,dtype='<f4').reshape(-1,channels).T
    if not np.isfinite(audio).all():raise ValueError('音轨含无效数值')
    if sr!=48000:audio=resample(audio,sr,48000)
    name=hashlib.sha256(row['stem'].encode()).hexdigest()[:16]+'.wav'
    sf.write(str(path.parent/name),audio.T,48000,subtype='PCM_24')
    outputs.append(dict(stem=row['stem'],label=label(row['stem']),file=name,frames=audio.shape[-1],channels=channels,sample_rate=48000))
   assert {o['stem'] for o in outputs}==set(job['stems'])
  job.update(status='succeeded',outputs=outputs,message='分离完成',seconds=round(time.time()-started,2),managedProvider='pymss',managedNativeResponse=metadata['id'])
 except Exception as exc:
  job.update(status='unknown' if submitted else 'failed',error=str(exc),message='输入和已有结果已保留，未自动重跑')
 finally:
  http.close();write(path,job)
