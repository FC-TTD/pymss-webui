"""Pinned official multilingual BandIt v2 artifact; range download + Zenodo checksum."""
import concurrent.futures,hashlib,subprocess
from pathlib import Path
root=Path('/mnt/TTD-Data/pymss-ui-preview/models/bandit-multi');root.mkdir(exist_ok=True)
size=446680129;url='https://zenodo.org/records/12701995/files/checkpoint-multi.ckpt?download=1'
def part(i):
 start=size*i//8;end=size*(i+1)//8-1;target=root/f'zenodo.part{i}'
 if not target.exists() or target.stat().st_size!=end-start+1:
  with (root/f'part{i}.log').open('w') as log:
   subprocess.run(['curl','-fsSL','--retry','2','--connect-timeout','15','--max-time','600','-r',f'{start}-{end}','-o',str(target),url],stdout=log,stderr=log,check=True)
 assert target.stat().st_size==end-start+1
 print('Part '+str(i)+' complete',flush=True);return target
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:parts=list(pool.map(part,range(8)))
target=root/'checkpoint-multi.original.ckpt';h=hashlib.md5()
with target.open('wb') as out:
 for part in parts:
  with part.open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):out.write(b);h.update(b)
assert target.stat().st_size==size and h.hexdigest()=='fea2868787551b0cff36cfcf7c3622a3'
print('Official BandIt multi MD5 verified',flush=True)
