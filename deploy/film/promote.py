"""Promote only the verified shared runtime after an idle fence; preserve data/devices."""
import argparse,json,subprocess,time
from pathlib import Path

NAME='pymss-preview-runtime'
BASE='sha256:77aab4346028ddfb2e17f7c96f5ddab8ffdbd5b3fce17dc90c9b4f0810aeca98'
PROBE="import json,urllib.request;print(json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:8000/healthz'))))"
def run(args,**kwargs):return subprocess.run(args,check=True,**kwargs)
def inspect(name):return json.loads(subprocess.check_output(['docker','inspect',name]))[0]
def health(name):return json.loads(subprocess.check_output(['docker','exec',name,'python','-c',PROBE]))
def main():
 p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--source',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 assert '@sha256:' in a.image
 old=inspect(NAME);assert old['Image']==BASE and old['State']['Running'],'Shared runtime drift: re-audit before promotion'
 assert not a.out.exists();a.out.mkdir(parents=True,mode=0o700)
 labels=old['Config']['Labels'];cmd=['docker','compose']
 if labels.get('com.docker.compose.project.environment_file'):cmd+=['--env-file',labels['com.docker.compose.project.environment_file']]
 for f in labels['com.docker.compose.project.config_files'].split(','):cmd+=['-f',f]
 desired=json.loads(subprocess.check_output(cmd+['config','--format','json']))
 assert desired['services']['runtime']['image']==old['Config']['Image']
 (a.out/'before.json').write_text(json.dumps(old));(a.out/'before-compose.json').write_text(json.dumps(desired))
 run(['docker','pull',a.image],stdout=subprocess.DEVNULL)
 proof=subprocess.check_output(['docker','run','--rm','--network','none','--entrypoint','cat',a.image,'/opt/song-studio-source-commit'],text=True).strip();assert proof==a.source
 for name in [NAME,'separation-film-runtime']:
  for _ in range(3):
   assert not health(name)['busy'],'Active inference: wait without stopping it'
   assert 'studio_runtime.worker' not in subprocess.check_output(['docker','top',name,'-eo','args'],text=True)
   time.sleep(1)
 assert set(old['NetworkSettings']['Networks'])=={'pymss-ui-preview_default'}
 run(['docker','network','disconnect','pymss-ui-preview_default',NAME])
 if health(NAME)['busy']:
  run(['docker','network','connect','--alias','runtime','pymss-ui-preview_default',NAME]);raise RuntimeError('A request arrived during idle fence; original service restored')
 run(['docker','stop','--timeout','-1',NAME],stdout=subprocess.DEVNULL)
 target=dict(desired);target['services']={'runtime':dict(desired['services']['runtime'])}
 service=target['services']['runtime'];service.pop('depends_on',None);service['image']=a.image
 service.setdefault('labels',{}).update({'ttd.song.transport.source':a.source,'ttd.film.source':a.source})
 file=a.out/'runtime-compose.json';file.write_text(json.dumps(target,indent=2))
 command=['docker','compose','--project-name','pymss-ui-preview','-f',str(file)]
 run(command+['config','--quiet']);run(command+['up','-d','--no-build','--no-deps','--pull','never','runtime'])
 deadline=time.monotonic()+60
 while True:
  try:
   if health(NAME)['status']=='ok':break
  except subprocess.CalledProcessError:pass
  if time.monotonic()>deadline:raise RuntimeError('Runtime not ready: apply before-compose.json to roll back, retaining data')
  time.sleep(1)
 new=inspect(NAME)
 assert old['Mounts']==new['Mounts']
 assert old['HostConfig']['DeviceRequests']==new['HostConfig']['DeviceRequests']
 assert old['HostConfig']['PortBindings']==new['HostConfig']['PortBindings']
 receipt=dict(source=a.source,image=a.image,container=new['Id'],mounts_devices_ports_preserved=True)
 (a.out/'applied.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
if __name__=='__main__':main()
