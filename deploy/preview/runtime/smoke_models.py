"""Serial real-audio smoke; availability is earned by actual CUDA output."""
import json,subprocess,sys,time
from pathlib import Path
from studio_runtime.worker import write,verification_key
manifest=json.loads(Path('/model-cache/download-manifest.json').read_text());state=Path('/data/verified-models.json');verified=json.loads(state.read_text()) if state.exists() else {}
for m in manifest['models']:
 if len(sys.argv)>1 and m['id'] not in sys.argv[1:]:continue
 if not m['downloaded'] or (verified.get(m['id'],{}).get('passed') and verified[m['id']].get('verification_key')==verification_key(m)):continue
 folder=Path('/data/smoke')/m['id'];folder.mkdir(parents=True,exist_ok=True);path=folder/'job.json'
 write(path,{'id':'smoke','model':m['id'],'filename':'real-song-clip.wav','input':'/data/smoke-input.wav','status':'queued','outputs':[]})
 start=time.time()
 with (folder/'worker.log').open('w') as log:p=subprocess.run([sys.executable,'-m','studio_runtime.worker',str(path)],stdout=log,stderr=log)
 result=json.loads(path.read_text());passed=not p.returncode and result['status']=='succeeded'
 verified[m['id']]={'passed':passed,'verification_key':verification_key(m),'stems':[{'id':o['stem'],'label':o['label']} for o in result.get('outputs',[])],'reason':'' if passed else result.get('error','运行中断'),'evidence':str(path),'seconds':round(time.time()-start,2)};write(state,verified)
 print(('PASS ' if passed else 'FAIL ')+m['id']+' '+str(verified[m['id']]['seconds'])+'s '+verified[m['id']]['reason'],flush=True)
