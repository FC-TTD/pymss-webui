#!/usr/bin/env bash
# Publish only the isolated static interaction preview to stage. Never changes Hub.
set -euo pipefail
project_root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$project_root"
npm run build:design
bundle_path="$(python3 - <<'PY'
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile
root=Path.cwd()
paths=[p for p in (root/'src').rglob('*') if p.is_file()]
paths += [root/p for p in ['package.json','package-lock.json','index.html','tsconfig.json','vite.config.ts','svelte.config.js']]
paths += [p for p in (root/'deploy/preview').rglob('*') if p.is_file() and p.name!='README.md' and '__pycache__' not in p.parts and p.suffix!='.pyc']
paths=sorted(set(paths))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source={str(p.relative_to(root)):sha(p) for p in paths}
provider=root.parent/'pymss'/'pymss'
runtime_input=root.parent/'pymss-ui-evidence'/'runtime-input'
extras={Path('provider/pymss')/p.relative_to(provider):p for p in provider.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
extras.update({p.relative_to(runtime_input):p for p in runtime_input.rglob('*') if p.is_file()})
source.update({str(k):sha(v) for k,v in extras.items()})
artifact={str(p.relative_to(root/'dist-design')):sha(p) for p in sorted((root/'dist-design').rglob('*')) if p.is_file()}
base=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
provider_base=subprocess.check_output(['git','-C',str(provider.parent),'rev-parse','HEAD'],text=True).strip()
identity={'source':source,'artifact':artifact,'provider_base_commit':provider_base,'base_commit':base,'scope':'real-separation-preview'}
raw=json.dumps(identity,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
release='h-'+hashlib.sha256(raw).hexdigest()[:16]
out=root.parent/'pymss-ui-evidence'/'stage-releases'/release
out.mkdir(parents=True,exist_ok=True)
for p in paths:
 target=out/'source'/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
shutil.copytree(root/'dist-design',out/'dist-design',dirs_exist_ok=True)
for rel,p in extras.items():
 target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
shutil.copytree(root/'deploy/preview/runtime',out/'runtime',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for filename in ['Dockerfile','Dockerfile.runtime','nginx.conf','compose.yaml','.dockerignore']:
 shutil.copy2(root/'deploy/preview'/filename,out/filename)
(out/'input-manifest.json').write_bytes(json.dumps(identity,ensure_ascii=False,indent=2).encode()+b'\n')
metadata={'provider_base_commit':provider_base,'release':release,'source_repository':'FC-TTD/pymss-webui','base_commit':base,'source_state':'uncommitted-preview-snapshot','input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'scope':'real-separation-preview','hub_changed':False}
(out/'release.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
(out/'.env').write_text('PREVIEW_RELEASE='+release+'\n')
archive=out.with_suffix('.tar.gz')
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(out.iterdir()):t.add(p,arcname=p.name)
print(archive)
PY
)"
release="$(basename "$bundle_path" .tar.gz)"
remote_root="/opt/pymss-ui-preview/releases/$release"
ssh -o BatchMode=yes -o ConnectTimeout=8 root@ttd-stage "mkdir -p '$remote_root'"
scp -q "$bundle_path" "root@ttd-stage:$remote_root/bundle.tar.gz"
ssh -o BatchMode=yes root@ttd-stage bash -s -- "$remote_root" "$release" "${EXPECTED_PREVIEW_RELEASE:-}" "${EXPECTED_WAITING_JOB:-}" <<'REMOTE'
set -euo pipefail
release_dir="$1"
release="$2"
expected_previous="${3:-}"
expected_waiting_job="${4:-}"
cd "$release_dir"
tar -xzf bundle.tar.gz
python3 - <<'PY'
import ipaddress,json,subprocess
candidate=ipaddress.ip_network('10.35.0.0/24')
assert not candidate.overlaps(ipaddress.ip_network('192.168.0.0/16'))
ids=subprocess.check_output(['docker','network','ls','-q'],text=True).split()
for network in json.loads(subprocess.check_output(['docker','network','inspect',*ids],text=True)):
    if network['Name']=='pymss-ui-preview_default': continue
    for item in (network.get('IPAM',{}).get('Config') or []):
        subnet=item.get('Subnet','')
        if subnet and ':' not in subnet:
            assert not candidate.overlaps(ipaddress.ip_network(subnet)), f'Network overlap: {network["Name"]} {subnet}'
for route in json.loads(subprocess.check_output(['ip','-j','-4','route'],text=True)):
    destination=route.get('dst','default')
    if destination=='default' or route.get('dev','').startswith(('br-','docker')): continue
    assert not candidate.overlaps(ipaddress.ip_network(destination,strict=False)), f'Route overlap: {destination}'
print('Network preflight passed: explicit10.35.0.0/24, no existing network/real-route overlap.')
PY
if docker inspect pymss-preview-runtime >/dev/null 2>&1; then
  test "$(docker inspect pymss-preview-runtime --format '{{index .Config.Labels "ttd.preview.owner"}}')" = pymss-webui
  docker exec -i pymss-preview-runtime python - "$expected_waiting_job" <<'PY'
import json,pathlib,sys,urllib.request
busy=json.load(urllib.request.urlopen('http://127.0.0.1:8000/healthz'))['busy']
if busy:
    expected=sys.argv[1]
    assert len(expected)==32 and all(c in '0123456789abcdef' for c in expected), 'Preview has an active upload/separation'
    active=[]
    for path in pathlib.Path('/data/jobs').glob('*/job.json'):
        state=json.loads(path.read_text())
        if state.get('status') in {'queued','running','waiting'}: active.append(state)
    assert len(active)==1 and active[0]['id']==expected and active[0]['status']=='waiting', 'Only the exact owned resource-wait job may be interrupted for its repair'
    print('Repairing the exact waiting job; its persistent input is retained and restart marks it interrupted.')
PY
  processes="$(docker top pymss-preview-runtime -eo pid,args)"
  if grep -Eq 'studio_runtime[.](worker|smoke_models)' <<< "$processes"; then
    echo 'A preview separation or model validation is active. Retry after it finishes.' >&2; exit 5
  fi
fi
previous_compose=''
if docker inspect pymss-ui-preview-web >/dev/null 2>&1; then
  previous="$(docker inspect pymss-ui-preview-web --format '{{index .Config.Labels "ttd.preview.release"}}')"
  if test "$previous" != "$release"; then
    test -n "$expected_previous" && test "$previous" = "$expected_previous" || { echo 'A different preview is running; set EXPECTED_PREVIEW_RELEASE after reviewing it.' >&2; exit 3; }
    test "$(docker inspect pymss-ui-preview-web --format '{{index .Config.Labels "ttd.preview.owner"}}')" = 'pymss-webui'
    docker inspect pymss-ui-preview-web --format '{{.Image}}' > previous-image.txt
    printf '%s\n' "$previous" > previous-release.txt
  fi
  previous_compose="$(docker inspect pymss-ui-preview-web --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}')"
else
  test -z "$(ss -H -ltn sport = :17896)" || { echo 'Port17896 already in use.' >&2; exit 4; }
fi
docker image inspect nginx@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10 >/dev/null
docker build --pull=false --network none --build-arg "PREVIEW_RELEASE=$release" -t "pymss-ui-preview:$release" . > build.log 2>&1
docker build --pull=false --network none -f Dockerfile.runtime -t "pymss-preview-runtime:$release" . > runtime-build.log 2>&1
docker compose --env-file .env -f compose.yaml config --quiet
if docker network inspect pymss-ui-preview_default >/dev/null 2>&1; then
  existing_subnet="$(docker network inspect pymss-ui-preview_default --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')"
  if test "$existing_subnet" != '10.35.0.0/24'; then
    test -n "$previous_compose" && test -f "$previous_compose"
    test "$(docker network inspect pymss-ui-preview_default --format '{{range .Containers}}{{.Name}}{{end}}')" = 'pymss-ui-preview-web'
    docker network inspect pymss-ui-preview_default > network-before.json
    ip route get 192.168.32.214 > home-route-before.txt
    mkdir -p previous-deployment
    cp "$previous_compose" previous-deployment/compose.yaml
    cp "$(dirname "$previous_compose")/.env" previous-deployment/.env
    # Stateless UI only; no -v, weights, Hub workloads or other networks touched.
    docker compose --env-file "$(dirname "$previous_compose")/.env" -f "$previous_compose" down --timeout 20
  fi
fi
docker compose --env-file .env -f compose.yaml up -d --no-build --pull never
docker network inspect pymss-ui-preview_default > network-after.json
ip route get 192.168.32.214 > home-route-after.txt
docker inspect pymss-ui-preview-web --format '{{.Id}} {{.Image}} {{json .NetworkSettings.Ports}}'
REMOTE
printf 'Preview release: %s\nPreview URL: http://ttd-stage:17896/ui/\nEvidence bundle: %s\n' "$release" "$bundle_path"
