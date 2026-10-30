"""Earn availability with serialized original CUDA worker and verified PCM outputs."""
import fcntl,json,os,subprocess,sys,time
from pathlib import Path
import numpy as np
import soundfile as sf
from studio_runtime.worker import verification_key

def write(path,data):
 temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(path)

def free_mb():
 r=subprocess.run(['nvidia-smi','-i',os.environ['STUDIO_GPU_UUID'],'--query-gpu=memory.free','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=5);return int(r.stdout.strip())

def priority(m):
 c=m.get('admission_category','');return (0 if c=='karaoke' else 1 if 'gender_chorus' in c else 2 if 'six_stem' in c else 3 if 'restoration' in c else 4 if 'mega_53' in c else 5,m['id'])

def main():
 manifest=json.loads(Path('/model-cache/download-manifest.json').read_text());state=Path('/data/verified-models.json');verified=json.loads(state.read_text()) if state.exists() else {};source=Path('/data/input.wav');info=sf.info(source);expected=round(info.frames/info.samplerate*48000)
 for m in sorted(manifest['models'],key=priority):
  if verified.get(m['id'],{}).get('verification_key')==verification_key(m):continue
  folder=Path('/data/smoke')/m['id'];folder.mkdir(parents=True,exist_ok=True);job=folder/'job.json';start=time.time()
  # Cooperate with the actual provider lock; never run a second model beside it.
  with open('/data/gpu-worker.lock','a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   if free_mb()<3072:
    print('WAIT capacity '+m['id'],flush=True);fcntl.flock(lock,fcntl.LOCK_UN);time.sleep(5);return
   write(job,dict(id='admission',model=m['id'],filename=source.name,input=str(source),status='queued',outputs=[]))
   with (folder/'worker.log').open('w') as log:
    try:r=subprocess.run([sys.executable,'-c','from studio_runtime.worker import run;import sys;run(sys.argv[1])',str(job)],stdout=log,stderr=log,timeout=180)
    except subprocess.TimeoutExpired:write(job,dict(status='failed',error='原生短片段测试超时',outputs=[]));r=None
   result=json.loads(job.read_text());passed=bool(r and r.returncode==0 and result.get('status')=='succeeded');reason=result.get('error','运行未完成');checks=[]
   if passed:
    try:
     for o in result['outputs']:
      p=folder/o['file'];a,sr=sf.read(p,dtype='float32',always_2d=True);i=sf.info(p)
      if sr!=48000 or len(a)!=expected or not np.isfinite(a).all() or i.subtype!='PCM_24':raise ValueError('输出帧数、采样率或数值不正确')
      checks.append(dict(stem=o['stem'],frames=len(a),sample_rate=sr,channels=a.shape[1],bytes=p.stat().st_size,peak=float(np.max(np.abs(a)))))
     if not checks:raise ValueError('没有有效输出')
    except Exception as e:passed=False;reason=str(e)
   verified[m['id']]=dict(passed=passed,verification_key=verification_key(m),stems=[dict(id=o['stem'],label=o['label']) for o in result.get('outputs',[])] if passed else [],reason='' if passed else reason,evidence=str(job),seconds=round(time.time()-start,2),peak_cuda_bytes=result.get('peak_cuda_bytes',0),output_checks=checks)
   write(state,verified)
  print(('PASS ' if passed else 'FAIL ')+m['id']+' '+str(verified[m['id']]['seconds'])+'s '+('' if passed else reason[:200]),flush=True)
 print('COMPLETE '+str(sum(v['passed'] for v in verified.values()))+'/'+str(len(verified)),flush=True)
if __name__=='__main__':main()
