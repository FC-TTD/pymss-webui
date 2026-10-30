"""Committed UI-only follow-ups; preserve the currently managed shared backends.

Run with source commit to build/update Stage, inspect that preview, then pass the
same commit and --formal to promote its immutable image. No model build/start.
"""
import argparse,hashlib,json,os,shlex,subprocess,tarfile,tempfile,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('commit');p.add_argument('--formal',action='store_true');a=p.parse_args()
def run(cmd,**kw):return subprocess.check_output(cmd,**kw)
def remote(host,cmd):return run(['ssh','-o','BatchMode=yes','root@'+host,cmd],text=True).strip()
def sha(b):return hashlib.sha256(b).hexdigest()
def info(host,name):
 d=json.loads(remote(host,shlex.join(['docker','inspect',name])))[0]
 labels=d['Config']['Labels']
 return dict(id=d['Id'],image=d['Image'],host=host,name=name,state=d['State']['Status'],management=labels.get('com.docker.compose.project.working_dir'),config_files=labels.get('com.docker.compose.project.config_files'),environment_file=labels.get('com.docker.compose.project.environment_file'))
assert run(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==a.commit
assert Path(__file__).read_bytes()==run(['git','-C',str(root),'show',a.commit+':deploy/unified/update_static.py'])
backends=[info(h,n) for h,n in [('ttd-stage','pymss-preview-runtime'),('ttd-stage','pymss-chain-preview'),('ttd-edge','clearvoice-audio-entry'),('ttd-edge','yingmusic-audio-entry')]]
assert all(d['state']=='running' for d in backends)
for name,count in [('studio',37),('speech',5),('ym',1)]:
 models=json.load(urllib.request.urlopen('http://msst/api/'+name+'/models',timeout=20))['models'];assert sum(m['available'] for m in models)==count
out=root.parent/'pymss-ui-evidence/static-followups'/a.commit;out.mkdir(parents=True,exist_ok=True)
if not a.formal:
 with tempfile.TemporaryDirectory() as td:
  snapshot=Path(td)/'source';snapshot.mkdir()
  archive=run(['git','-C',str(root),'archive',a.commit])
  import io
  with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(snapshot,filter='data')
  files=[f for f in snapshot.rglob('*') if f.is_file()]
  before={str(f.relative_to(snapshot)):sha(f.read_bytes()) for f in files}
  for f in files:f.chmod(0o444)
  (snapshot/'node_modules').symlink_to(root/'node_modules',target_is_directory=True)
  subprocess.run(['npm','run','build:design'],cwd=snapshot,check=True)
  assert all(sha((snapshot/n).read_bytes())==h for n,h in before.items())
  import shutil
  shutil.copytree(snapshot/'dist-design',out/'dist-design',dirs_exist_ok=True)
  for source,target in [('deploy/preview/Dockerfile','Dockerfile'),('deploy/preview/nginx.conf','nginx.conf'),('deploy/preview/compose.yaml','compose.yaml'),('deploy/unified/compose.yaml','unified-compose.yaml')]:shutil.copyfile(snapshot/source,out/target)
 artifact={str(f.relative_to(out/'dist-design')):sha(f.read_bytes()) for f in (out/'dist-design').rglob('*') if f.is_file()}
 manifest=dict(source_commit=a.commit,source=before,artifact=artifact,backends=backends,scope='static-only-existing-backends')
 release='h-'+sha(json.dumps(manifest,sort_keys=True).encode())[:16]
 (out/'input-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'release.json').write_text(json.dumps(dict(release=release,source_commit=a.commit))+'\n')
 (out/'.dockerignore').write_text('*\n!Dockerfile\n!nginx.conf\n!release.json\n!dist-design/\n!dist-design/**\n')
else:
 manifest=json.loads((out/'input-manifest.json').read_text());release=json.loads((out/'release.json').read_text())['release']
 assert manifest['source_commit']==a.commit and manifest['backends']==backends,'Shared dependencies changed; revalidate Stage.'
 for name,h in manifest['artifact'].items():assert sha(urllib.request.urlopen('http://ttd-stage:17896/ui/'+name,timeout=20).read())==h
remote_dir='/opt/audio-separation/static-followups/'+release
if not a.formal:
 bundle=out/'bundle.tar.gz'
 with tarfile.open(bundle,'w:gz') as tar:
  for f in out.iterdir():
   if f!=bundle:tar.add(f,arcname=f.name)
 remote('ttd-stage','mkdir -p '+shlex.quote(remote_dir))
 subprocess.run(['scp','-q',str(bundle),'root@ttd-stage:'+remote_dir+'/'],check=True)
 command=r'''
set -eu
cd "$1"
tar -xzf bundle.tar.gz
docker image inspect nginx@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10 >/dev/null
docker build --provenance=false --pull=false --network none --build-arg PREVIEW_RELEASE="$2" -t audio-static:"$2" . > build.log 2>&1
first_image="$(docker image inspect audio-static:"$2" --format '{{.Id}}')"
docker build --provenance=false --pull=false --network none --build-arg PREVIEW_RELEASE="$2" -t audio-static:"$2" . > repeat-build.log 2>&1
test "$first_image" = "$(docker image inspect audio-static:"$2" --format '{{.Id}}')"
grep -q CACHED repeat-build.log
'''
 subprocess.run(['ssh','-o','BatchMode=yes','root@ttd-stage','bash','-s','--',remote_dir,release],input=command,text=True,check=True)
image=remote('ttd-stage','docker image inspect '+shlex.quote('audio-static:'+release)+' --format '+shlex.quote('{{.Id}}'))
name='audio-separation-entry' if a.formal else 'pymss-ui-preview-web';previous=info('ttd-stage',name)
assert previous['management'] and previous['management'].startswith('/opt/')
(out/('formal-before.json' if a.formal else 'stage-before.json')).write_text(json.dumps(previous,indent=2))
for d in backends:assert info(d['host'],d['name'])==d,'A shared backend changed before update.'
settings=dict(image=image,release=release,source_commit=a.commit,backends=backends,previous=previous)
(out/('formal.json' if a.formal else 'stage.json')).write_text(json.dumps(settings,indent=2))
# Only the selected CPU web service is reconciled; the runtime definition is
# not applied. Existing explicit 10.35 network and private ports remain intact.
config=dict(services={'entry' if a.formal else 'web':dict(image=image,labels={'ttd.audio.source' if a.formal else 'ttd.preview.source':a.commit,'ttd.audio.release' if a.formal else 'ttd.preview.release':release})})
phase='formal' if a.formal else 'stage';env=f'AUDIO_UI_IMAGE={image}\nAUDIO_SOURCE_COMMIT={a.commit}\nAUDIO_RELEASE={release}\nPREVIEW_RELEASE={release}\n'
(out/(phase+'.env')).write_text(env);(out/(phase+'-override.json')).write_text(json.dumps(config))
subprocess.run(['scp','-q',str(out/(phase+'.env')),str(out/(phase+'-override.json')),str(out/(phase+'.json')),'root@ttd-stage:'+remote_dir+'/'],check=True)
compose='unified-compose.yaml' if a.formal else 'compose.yaml';service='entry' if a.formal else 'web'
cmd=['docker','compose','--project-name','audio-separation' if a.formal else 'pymss-ui-preview','--env-file',phase+'.env','-f',compose,'-f',phase+'-override.json']
remote('ttd-stage','cd '+shlex.quote(remote_dir)+' && '+shlex.join(cmd+['config','--quiet']))
remote('ttd-stage','cd '+shlex.quote(remote_dir)+' && '+shlex.join(cmd+['up','-d','--no-deps','--no-build','--pull','never',service]))
for d in backends:assert info(d['host'],d['name'])==d,'Shared backend identity changed.'
print(json.dumps(dict(phase=phase,release=release,image=image,management=remote_dir,previous=previous),indent=2))
