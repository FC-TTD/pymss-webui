from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile,tempfile
root=Path(__file__).resolve().parents[2]
files=[p for p in (root/'deploy/chain').glob('*') if p.is_file() and p.suffix!='.pyc']
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
release='h-'+hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()[:16];remote='/opt/pymss-chain-preview/releases/'+release
with tempfile.TemporaryDirectory() as t:
 folder=Path(t)
 for p in files:
  q=folder/p.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 shutil.copy2(root/'deploy/chain/Dockerfile',folder/'Dockerfile');shutil.copy2(root/'deploy/chain/compose.yaml',folder/'compose.yaml')
 (folder/'.dockerignore').write_text('*\n!deploy/\n!deploy/chain/\n!deploy/chain/app.py\n')
 (folder/'.env').write_text('CHAIN_RELEASE='+release+'\n');(folder/'input-manifest.json').write_text(json.dumps(manifest,indent=2))
 archive=folder/'bundle.tar.gz'
 with tarfile.open(archive,'w:gz') as tar:
  for p in folder.iterdir():
   if p!=archive:tar.add(p,arcname=p.name)
 subprocess.run(['ssh','-o','BatchMode=yes','root@ttd-stage','mkdir -p '+remote],check=True);subprocess.run(['scp','-q',str(archive),'root@ttd-stage:'+remote+'/'],check=True)
cmd=r'''
set -euo pipefail
cd "$1"; tar -xzf bundle.tar.gz
test "$(docker image inspect pymss-preview-runtime:h-bd63eb3d3ceeebfe --format '{{.Id}}')" = sha256:5e7c82a2dadc149114ad379ccc396b58f7b6302eb4bb10a8b54d038e13a584b8
test "$(docker network inspect pymss-ui-preview_default --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')" = 10.35.0.0/24
test "$(findmnt -T /mnt/TTD -n -o FSTYPE)" = nfs4
if docker inspect pymss-chain-preview >/dev/null 2>&1; then
 test "$(docker inspect pymss-chain-preview --format '{{index .Config.Labels "ttd.preview.owner"}}')" = pymss-webui
 test "$(docker exec pymss-chain-preview python -c "import urllib.request,json;print(json.load(urllib.request.urlopen('http://127.0.0.1:8000/healthz'))['busy'])")" = False
 docker inspect pymss-chain-preview > previous-container.json
fi
mkdir -p /mnt/TTD/04_应用/pymss-chain-preview
ip route get 192.168.32.214 > home-route-before.txt
docker build --pull=false --network none -t pymss-chain-preview:"$2" . > build.log 2>&1
docker compose --env-file .env config --quiet
docker compose --env-file .env up -d --no-build --pull never
ip route get 192.168.32.214 > home-route-after.txt
docker inspect pymss-chain-preview --format '{{.Image}} {{.State.Status}}'
'''
subprocess.run(['ssh','-o','BatchMode=yes','root@ttd-stage','bash','-s','--',remote,release],input=cmd,text=True,check=True);print('Chain preview:',release,remote)
