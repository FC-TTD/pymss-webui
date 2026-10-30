"""Atomically append reviewed additions; preserve all existing assets and verification.
Caller supplies the frozen admission source and evidence after PR validation.
No service restart, worker/model changes, weight overwrite or data deletion.
"""
import argparse,fcntl,json,os
from pathlib import Path

def serialize(v):return json.dumps(v,ensure_ascii=False,indent=2)+'\n'
def atomic(p,v):
 temp=p.with_name(p.name+'.catalog.tmp');temp.write_text(serialize(v));temp.replace(p)
def publish(manifest,verified,candidates,evidence,backup,requirements=None):
 m0=manifest.read_text();v0=verified.read_text();r0=requirements.read_text() if requirements and requirements.exists() else '{}';r=json.loads(r0);m=json.loads(m0);v=json.loads(v0);old={row['id'] for row in m['models']};added=[]
 for row in candidates['models']:
  if row['id'] in old:continue
  record=evidence.get(row['id'])
  if not record:raise ValueError('Missing admission result: '+row['id'])
  m['models'].append(row);v[row['id']]=record;added.append(row['id'])
  if record.get('passed') and record.get('peak_cuda_bytes'):r[row['id']]=max(r.get(row['id'],0),record['peak_cuda_bytes'])
 if manifest.read_text()!=m0 or verified.read_text()!=v0 or requirements and (requirements.read_text() if requirements.exists() else '{}')!=r0:raise RuntimeError('Concurrent registry update; nothing written')
 backup.mkdir(parents=True,exist_ok=True)
 for name,text in [('manifest-before.json',m0),('verification-before.json',v0),('requirements-before.json',r0)]:
  path=backup/name
  if path.exists() and path.read_text()!=text:raise RuntimeError('Backup already exists; do not overwrite')
  path.write_text(text)
 # Publish results first: unregistered verified IDs cannot yet be selected.
 atomic(verified,v)
 if requirements:atomic(requirements,r)
 if manifest.read_text()!=m0:raise RuntimeError('Concurrent manifest update; verification additions remain inert')
 atomic(manifest,m)
 return added

def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--verified',type=Path,required=True);p.add_argument('--candidates',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--backup',type=Path,required=True);p.add_argument('--lock',type=Path,required=True);p.add_argument('--requirements',type=Path);a=p.parse_args()
 with a.lock.open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);added=publish(a.manifest,a.verified,json.loads(a.candidates.read_text()),json.loads(a.evidence.read_text()),a.backup,a.requirements)
 print(json.dumps({'added':len(added),'ids':added},ensure_ascii=False))
if __name__=='__main__':main()
