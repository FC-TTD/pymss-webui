"""Promote a verified CPU UI artifact; never rebuild or alter either GPU runtime.

Requires a separately authorized source commit. Without --apply this is read-only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import time
import urllib.request

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('release')
parser.add_argument('source_commit')
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
assert re.fullmatch(r'h-[0-9a-f]{16}', args.release)
assert re.fullmatch(r'[0-9a-f]{40}', args.source_commit)

def git(*cmd):
    return subprocess.check_output(['git', '-C', str(root), *cmd])

assert git('rev-parse', 'HEAD').decode().strip() == args.source_commit
assert Path(__file__).read_bytes() == git('show', f'{args.source_commit}:deploy/unified/publish.py')
bundle = root.parent / 'pymss-ui-evidence/stage-releases' / args.release
manifest = json.loads((bundle / 'input-manifest.json').read_text())
identity = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
assert 'h-' + hashlib.sha256(identity).hexdigest()[:16] == args.release, 'Candidate manifest identity mismatch.'
verified = 0
for name, expected in manifest['source'].items():
    if (root / name).is_file():
        data = git('show', f'{args.source_commit}:{name}')  # Untracked inputs fail closed.
        assert hashlib.sha256(data).hexdigest() == expected, name
        verified += 1
compose = git('show', f'{args.source_commit}:deploy/unified/compose.yaml')
required = {'src/App.svelte', 'src/lib/studio/AudioWorkspace.svelte',
            'src/lib/studio/Studio.svelte', 'deploy/preview/nginx.conf',
            'deploy/preview/runtime/app.py', 'deploy/preview/runtime/batch.py',
            'deploy/preview/runtime/worker.py', 'package-lock.json'}
assert required.issubset(manifest['source']) and verified >= len(required)

def ssh(host, command):
    return subprocess.check_output(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'root@' + host, command], text=True).strip()

image = ssh('ttd-stage', f'docker image inspect pymss-ui-preview:{args.release} --format '+shlex.quote('{{.Id}}'))
runtime_release = ssh('ttd-stage', 'docker inspect pymss-preview-runtime --format '+shlex.quote('{{index .Config.Labels "ttd.preview.release"}}'))
assert runtime_release == args.release, 'The tested backend release changed; re-verify before promotion.'
backend_subnet = ssh('ttd-stage', 'docker network inspect pymss-ui-preview_default --format '+shlex.quote('{{range .IPAM.Config}}{{.Subnet}}{{end}}'))
assert backend_subnet == '10.35.0.0/24'
caddy_id = ssh('ttd-edge', 'docker network inspect caddy --format '+shlex.quote('{{.Id}}'))
assert re.fullmatch(r'[a-z0-9]{20,32}', caddy_id)
promotion = dict(source_commit=args.source_commit, release=args.release, ui_image=image,
                 verified_committed_ui_inputs=verified, backend_release=runtime_release,
                 caddy_network=caddy_id, caddy_network_name='caddy', private_origin='http://msst/', native='http://msst/?native=msst',
                 runtime_policy='Existing PYMSS Stage backend and original Hub MSST entry unchanged; no GPU deployment/migration.')
print(json.dumps(promotion, ensure_ascii=False, indent=2), flush=True)
if not args.apply:
    raise SystemExit('Read-only preflight passed; --apply is required for the authorized private entry publication.')

remote = f'/opt/audio-separation/releases/{args.release}-{args.source_commit[:12]}'
ssh('ttd-stage', 'mkdir -p '+shlex.quote(remote))
with tempfile.TemporaryDirectory() as directory:
    folder = Path(directory)
    (folder / 'compose.yaml').write_bytes(compose)
    (folder / 'promotion-source.json').write_text(json.dumps(promotion, ensure_ascii=False, indent=2)+'\n')
    (folder / '.env').write_text(f'AUDIO_UI_IMAGE={image}\nAUDIO_SOURCE_COMMIT={args.source_commit}\nAUDIO_RELEASE={args.release}\nCADDY_NETWORK_ID={caddy_id}\n')
    subprocess.run(['scp', '-q', str(folder/'compose.yaml'), str(folder/'.env'), str(folder/'promotion-source.json'), 'root@ttd-stage:'+remote+'/'], check=True)
command = shlex.join(['bash', '-s', '--', remote])
subprocess.run(['ssh', '-o', 'BatchMode=yes', 'root@ttd-stage', command], input=r'''
set -euo pipefail
cd "$1"
if docker inspect audio-separation-entry >/dev/null 2>&1; then
  test "$(docker inspect audio-separation-entry --format '{{index .Config.Labels "ttd.audio.owner"}}')" = pymss-webui
  docker inspect audio-separation-entry > previous-container.json
fi
ip route get 192.168.32.214 > home-route-before.txt
docker compose --env-file .env -f compose.yaml config --quiet
docker compose --env-file .env -f compose.yaml up -d --no-build --pull never
ip route get 192.168.32.214 > home-route-after.txt
docker inspect audio-separation-entry --format '{{.Image}} {{.State.Status}}'
''', text=True, check=True)

# Caddy merges only private /, /ui/* and /api/studio/* handles with the unchanged
# MSST catch-all. No public proxy labels, native admission paths or Hub config change.
for _ in range(30):
    try:
        page = urllib.request.urlopen('http://msst/ui/', timeout=3).read()
        if hashlib.sha256(page).hexdigest() == manifest['artifact']['index.html']:
            break
    except Exception:
        pass
    time.sleep(2)
else:
    raise SystemExit('Private route did not match the tested UI. Keep the portal unchanged and inspect Caddy; no GPU runtime was altered.')
native = urllib.request.urlopen('http://msst/?native=msst').read()
assert b'window.gradio_config' in native
models = json.load(urllib.request.urlopen('http://msst/api/studio/models'))['models']
assert sum(model['available'] for model in models) == 37
print('Private entry published; verify browser default/switch/input reuse before updating the portal card.')
