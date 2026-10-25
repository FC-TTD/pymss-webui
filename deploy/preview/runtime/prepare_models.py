"""Download only missing review-list weights; verify pinned upstream LFS hashes.
Existing shared PYMSS weights are read-only inputs; additions use preview-owned storage.
"""
import concurrent.futures, hashlib, json, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/mnt/TTD-Data/pymss-ui-preview/models')
SHARED=Path('/mnt/TTD-Data/pymss/models')

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()

def fetch(repo, revision, spec, target):
 rel=spec['rfilename']; sha=spec.get('lfs',{}).get('sha256'); size=spec.get('size')
 if target.is_file() and target.is_relative_to(SHARED):
  if (size and target.stat().st_size!=size) or (sha and digest(target)!=sha):
   print('Preserve administrator cache; use pinned preview copy: '+rel,flush=True)
   target=ROOT/target.relative_to(SHARED)
 target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():
  partial=target.with_name(target.name+'.partial')
  for host in ['https://hf-mirror.com','https://huggingface.co']:
   cmd=['curl','-fL','--retry','2','--connect-timeout','15','--max-time','900','--speed-limit','1024','--speed-time','60','-C','-','-o',str(partial),f'{host}/{repo}/resolve/{revision}/{rel}']
   with (target.parent/(target.name+'.download.log')).open('a') as log:
    ok=subprocess.run(cmd,stdout=log,stderr=log).returncode==0
   if ok:
    if (size and partial.stat().st_size!=size) or (sha and digest(partial)!=sha):raise ValueError('Downloaded integrity mismatch: '+rel)
    partial.rename(target);break
  else:raise RuntimeError('Download failed: '+rel)
 actual=digest(target)
 if size and target.stat().st_size!=size:raise ValueError('Cached size mismatch: '+rel)
 if sha and actual!=sha:raise ValueError('Cached SHA256 mismatch: '+rel)
 return {'path':str(target),'bytes':target.stat().st_size,'sha256':actual,'source':f'https://huggingface.co/{repo}/resolve/{revision}/{rel}'}

catalog=json.loads((HERE/'hf-catalog.json').read_text());index={x['rfilename']:x for x in catalog['siblings']}
rows=[]
for item in json.loads((HERE/'catalog-input.json').read_text()):
 paths=[item['relpath'],item['config_relpath']]
 rows.append({'id':item['name'],'type':item['model_type'],'files':[( 'baicai1145/pymss',catalog['sha'],index[x],SHARED/x if (SHARED/x).is_file() else ROOT/x) for x in paths]})
leap=json.loads((HERE/'hf-leap.json').read_text());ix={x['rfilename']:x for x in leap['siblings']}
for part in ['voc','inst']:
 names=[f'Xe/bs_leap_xe_{part}.ckpt',f'Xe/leap_xe_config_{part}.yaml']
 rows.append({'id':f'bs_leap_xe_{part}.ckpt','type':'bs_roformer','files':[('pcunwa/BS-Roformer-Leap',leap['sha'],ix[n],ROOT/'leap-xe'/Path(n).name) for n in names]})
dbs=json.loads((HERE/'hf-dbs.json').read_text());ix={x['rfilename']:x for x in dbs['siblings']}
rows.append({'id':'DBS-TIGER-DnR','type':'dbs_tiger','files':[('JusperLee/DBS-TIGER-DnR',dbs['sha'],ix[n],ROOT/'dbs-tiger'/n) for n in ['model.safetensors','config.json']]})
def prepare(item):
 row={k:v for k,v in item.items() if k!='files'}
 try:
  row['artifacts']=[fetch(*x) for x in item['files']];row['downloaded']=True;print('READY '+row['id'],flush=True)
 except Exception as e:row['downloaded']=False;row['error']=str(e);print('FAILED '+row['id']+' '+str(e),flush=True)
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(prepare,rows))
manifest_path=ROOT.parent/'download-manifest.json'
if manifest_path.exists():
 for row in json.loads(manifest_path.read_text()).get('models',[]):
  if row['id']=='bandit_v2_multi.ckpt' and row.get('downloaded') and all(Path(a['path']).is_file() and digest(Path(a['path']))==a['sha256'] for a in row['artifacts']):results.append(row)
(ROOT.parent/'download-manifest.json').write_text(json.dumps({'models':results},ensure_ascii=False,indent=2)+'\n')
print('Downloaded '+str(sum(r['downloaded'] for r in results))+'/'+str(len(results)),flush=True)
