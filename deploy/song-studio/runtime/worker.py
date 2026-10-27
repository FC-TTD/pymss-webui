"""One GPU process per separation; exit releases all model allocations."""
import hashlib,json,sys,time,traceback
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

LABELS={'vocals':'人声','instrumental':'伴奏','other':'其余声音','speech':'对白','music':'配乐','effects':'音效','sfx':'音效','crowd':'人群声','aspiration':'呼吸气声','dry':'清理后声音','noreverb':'干声','reverb':'混响','karaoke':'和声'}
def label(key):return LABELS.get(key.lower(),key)
def write(path,data):
 temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
def resample(audio,old,new):
 from math import gcd
 d=gcd(int(old),int(new));return resample_poly(audio,new//d,old//d,axis=-1).astype('float32')

def verification_key(model):
 return hashlib.sha256((Path(__file__).read_text()+json.dumps(model.get('artifacts',[]),sort_keys=True)+'pymss2.1.5-core0.1.8').encode()).hexdigest()

def run(job_path):
 job_path=Path(job_path);job=json.loads(job_path.read_text());started=time.time()
 try:
  import torch
  if not torch.cuda.is_available():raise RuntimeError('测试服务的 GPU 暂不可用，请稍后再试。')
  manifest=json.loads(Path('/model-cache/download-manifest.json').read_text())
  model=next(m for m in manifest['models'] if m['id']==job['model'])
  if not model['downloaded']:raise RuntimeError('模型文件尚未下载完成。')
  job.update(status='running',message='正在加载模型…');write(job_path,job)
  model_file,config_file=[a['path'] for a in model['artifacts']]
  if model['type']=='dbs_tiger':
   from dbs.models import DBSTIGER
   from dbs.engine import separate
   instance=DBSTIGER.from_pretrained(str(Path(model_file).parent)).eval().cuda()
   audio,sr=sf.read(job['input'],dtype='float32',always_2d=True);mix=audio.mean(1)[None,:];mix=resample(mix,sr,44100) if sr!=44100 else mix;sr=44100
   job.update(message='正在分离对白、配乐与音效…');write(job_path,job)
   with torch.inference_mode():out=separate(instance,torch.from_numpy(mix).unsqueeze(0).cuda(),{'mode':'chunked','chunk_seconds':6.,'hop_seconds':3.},sample_rate=sr)[0]
   results={key:out[i].detach().float().cpu().numpy().reshape(1,-1) for i,key in enumerate(['music','sfx','speech'])}
  else:
   from pymss import MSSeparator
   from pymss.config import load_config
   from pymss.audio_io import load_audio
   config=load_config(config_file);sr=int(config.audio.get('sample_rate',44100));mix,_=load_audio(job['input'],sr=sr,mono=False)
   # Native batch-size parameter reduces concurrent chunks; no precision/offload/device substitution.
   instance=MSSeparator(model['type'],model_file,config_path=config_file,device='cuda',device_ids=[0],inference_params={'batch_size':1})
   job.update(message='正在分离音轨…');write(job_path,job)
   results=instance.separate(mix,pbar=False)
  outputs=[];allowed=job.get('stems') or list(results)
  for key,audio in results.items():
   if key not in allowed:continue
   arr=np.asarray(audio,dtype='float32')
   # PYMSS returns sample-first arrays; native DBS returns channel-first.
   if model['type']!='dbs_tiger' and arr.ndim==2:arr=arr.T
   if arr.ndim==1:arr=arr[None,:]
   if not np.isfinite(arr).all():raise RuntimeError('模型输出含无效数值，无法导出。')
   if sr!=48000:arr=resample(arr,sr,48000)
   name=hashlib.sha256(key.encode()).hexdigest()[:16]+'.wav';target=job_path.parent/name
   sf.write(str(target),arr.T,48000,subtype='PCM_24')
   outputs.append({'stem':key,'label':label(key),'file':name,'frames':arr.shape[-1],'channels':arr.shape[0],'sample_rate':48000})
  if not outputs:raise RuntimeError('所选音轨与模型输出不匹配，请重新选择。')
  job.update(status='succeeded',message='分离完成',outputs=outputs,seconds=round(time.time()-started,2),peak_cuda_bytes=torch.cuda.max_memory_allocated())
 except Exception as exc:
  traceback.print_exc();job.update(status='failed',error=str(exc),outputs=[])
 write(job_path,job)
if __name__=='__main__':
 import fcntl
 with open('/data/gpu-worker.lock','a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  run(sys.argv[1])
