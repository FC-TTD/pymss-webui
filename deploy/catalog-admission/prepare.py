"""Inventory existing read-only weights; create an isolated, pinned admission manifest.
No weight download, global manifest update, model conversion or existing verification writes.
"""
import argparse,hashlib,json,subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()

def prepare(snapshot,hf,root,current,config_root=None):
 catalog={x['id']:x['pymss'] for x in snapshot['data']};index={x['rfilename']:x for x in hf['siblings']};registered={x['id'] for x in current['models']};rows=[];excluded=[]
 if config_root:
  def fetch_config(weight):
   if not weight.is_file() or weight.suffix not in {'.ckpt','.pth','.th'} or weight.name in registered or weight.name not in catalog:return
   rel=str(weight.with_suffix('.yaml').relative_to(root));spec=index.get(rel)
   if not spec:return
   path=config_root/rel;path.parent.mkdir(parents=True,exist_ok=True)
   if not path.exists():
    temp=path.with_suffix('.partial');url=f"https://huggingface.co/{hf['id']}/resolve/{hf['sha']}/{rel}"
    subprocess.run(['curl','-fLsS','--retry','2','--connect-timeout','15','--max-time','60','-o',str(temp),url],check=True);temp.replace(path)
  with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(fetch_config,root.rglob('*')))
 for weight in sorted(root.rglob('*')):
  if not weight.is_file() or weight.suffix not in {'.ckpt','.pth','.th'} or weight.name in registered:continue
  meta=catalog.get(weight.name)
  if not meta:excluded.append({'id':weight.name,'reason':'缺少已固定来源的目录与架构记录'});continue
  config=config_root/weight.with_suffix('.yaml').relative_to(root) if config_root else weight.with_suffix('.yaml');artifacts=[];reason=''
  for path in (weight,config):
   rel=str(path.relative_to(config_root if config_root and path.is_relative_to(config_root) else root));spec=index.get(rel)
   if not spec or not path.is_file():reason='缺少配置或固定版本来源';break
   sha=digest(path);expected=spec.get('lfs',{}).get('sha256')
   blob=hashlib.sha1(b'blob '+str(path.stat().st_size).encode()+b'\0'+path.read_bytes()).hexdigest() if not expected and path.stat().st_size<1024**2 else None
   if path.stat().st_size!=spec['size'] or expected and sha!=expected or not expected and blob!=spec.get('blobId'):reason='已有'+('配置' if path.suffix=='.yaml' else '权重')+'与固定来源校验不一致';break
   artifacts.append(dict(path=str(path),bytes=path.stat().st_size,sha256=sha,source=f"https://huggingface.co/{hf['id']}/resolve/{hf['sha']}/{rel}"))
  if reason:excluded.append({'id':weight.name,'reason':reason});continue
  rows.append(dict(id=weight.name,type=meta['model_type'],artifacts=artifacts,downloaded=True,admission_category=meta['category'],declared_target=meta['target_stem']))
 return {'models':rows,'excluded':excluded}

def main():
 p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--hf',type=Path,required=True);p.add_argument('--root',type=Path,default=Path('/mnt/TTD-Data/pymss/models'));p.add_argument('--current',type=Path,default=Path('/model-cache/download-manifest.json'));p.add_argument('--out',type=Path,required=True);p.add_argument('--config-root',type=Path);a=p.parse_args()
 result=prepare(json.loads(a.snapshot.read_text()),json.loads(a.hf.read_text()),a.root,json.loads(a.current.read_text()),a.config_root);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'candidates':len(result['models']),'excluded':result['excluded']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
