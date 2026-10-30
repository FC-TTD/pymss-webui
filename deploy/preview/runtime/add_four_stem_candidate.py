"""Add one pinned four-stem alternative; real smoke remains required for availability.
Run on Stage host with the existing preview cache mounted. Never rewrites shared weights.
"""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path('/mnt/TTD-Data/pymss-ui-preview')
REV='f02318ef92c43472777ed7aeeded3d2b29a68b58'
NAME='bs_roformer_4stems_ft.ckpt'
SPECS=[(NAME,527245586,'a64c61c5972fe3fdf331d98f06bb4d6e237147c83a4bc71fd4e00e254c9b7652'),('bs_roformer_4stems_ft.yaml',3344,None)]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def main():
 artifacts=[]
 for filename,size,expected in SPECS:
  path=ROOT/'models/music_stems/four_stem'/filename;path.parent.mkdir(parents=True,exist_ok=True)
  url=f'https://huggingface.co/baicai1145/pymss/resolve/{REV}/music_stems/four_stem/{filename}'
  if not path.exists():
   partial=path.with_suffix(path.suffix+'.partial')
   subprocess.run(['curl','-fL','--retry','2','--connect-timeout','15','--max-time','900','-C','-','-o',str(partial),url],check=True)
   if partial.stat().st_size!=size or expected and sha(partial)!=expected:raise RuntimeError('Candidate integrity mismatch')
   partial.rename(path)
  digest=sha(path)
  if path.stat().st_size!=size or expected and digest!=expected:raise RuntimeError('Cached candidate integrity mismatch')
  artifacts.append(dict(path=str(path),bytes=size,sha256=digest,source=url))
 manifest=ROOT/'download-manifest.json';before=manifest.read_text();data=json.loads(before)
 row=dict(id=NAME,type='bs_roformer',artifacts=artifacts,downloaded=True)
 prior=next((r for r in data['models'] if r['id']==NAME),None)
 if prior and prior!=row:raise RuntimeError('Existing candidate differs; preserve it for review')
 if not prior:data['models'].append(row)
 if manifest.read_text()!=before:raise RuntimeError('Concurrent manifest update; retry without overwriting')
 temp=manifest.with_suffix('.candidate.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(manifest)
 print('Prepared one candidate; not marked available until native CUDA smoke passes')
if __name__=='__main__':main()
