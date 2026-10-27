"""Promote the tested CPU entry. --prepare performs read-only working-tree checks.

Formal --apply requires separately authorized commits for all three repositories.
Existing managed inference/chain services are pinned external dependencies; no
GPU service, preview service, data, portal or public route is replaced here.
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
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('release')
parser.add_argument('source_commit', nargs='?')
parser.add_argument('--speech-commit')
parser.add_argument('--ying-commit')
parser.add_argument('--prepare', action='store_true')
parser.add_argument('--apply', action='store_true')
parser.add_argument('--expected-current-release', default='h-bd63eb3d3ceeebfe')
args = parser.parse_args()
assert re.fullmatch(r'h-[0-9a-f]{16}', args.release)
assert not (args.prepare and args.apply), 'Preparation cannot perform formal writes.'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(checkout, *cmd):
    return subprocess.check_output(['git', '-C', str(checkout), *cmd])


def source(checkout, commit, name):
    assert not Path(name).is_absolute() and '..' not in Path(name).parts
    if args.prepare:
        return (checkout / name).read_bytes()
    assert commit and re.fullmatch(r'[0-9a-f]{40}', commit), 'All source commits are required.'
    return git(checkout, 'show', f'{commit}:{name}')


def ssh(host, command):
    return subprocess.check_output(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8',
                                    'root@' + host, command], text=True).strip()


def inspect(host, name):
    return json.loads(ssh(host, shlex.join(['docker', 'inspect', name])))[0]


def get_json(url):
    return json.load(urllib.request.urlopen(url, timeout=20))


if not args.prepare:
    for checkout, commit in [(root, args.source_commit),
                             (root.parent / 'clearvoice-audio-api', args.speech_commit),
                             (root.parent / 'yingmusic-audio-api', args.ying_commit)]:
        assert commit and re.fullmatch(r'[0-9a-f]{40}', commit), 'Provide all three authorized source commits.'
        assert git(checkout, 'rev-parse', 'HEAD').decode().strip() == commit
    assert Path(__file__).read_bytes() == source(root, args.source_commit, 'deploy/unified/publish.py')

bundle = root.parent / 'pymss-ui-evidence/stage-releases' / args.release
manifest = json.loads((bundle / 'input-manifest.json').read_text())
identity = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
assert 'h-' + sha(identity)[:16] == args.release, 'Candidate identity mismatch.'
verified = 0
for name, expected in manifest['source'].items():
    # Foreign inputs belong to the already pinned backend snapshot; never let
    # a missing task-owned file silently bypass the source-of-truth gate.
    if not name.startswith(('provider/', 'dbs-source/', 'runtime-wheels/')):
        assert sha(source(root, args.source_commit, name)) == expected, name
        verified += 1
required = {'src/App.svelte', 'src/lib/studio/AudioWorkspace.svelte',
            'src/lib/studio/Studio.svelte', 'deploy/preview/nginx.conf',
            'deploy/preview/runtime/app.py', 'deploy/preview/runtime/batch.py',
            'deploy/preview/runtime/worker.py', 'package-lock.json'}
assert required.issubset(manifest['source']) and verified >= len(required)
compose = source(root, args.source_commit, 'deploy/unified/compose.yaml')
for prefix in ['studio', 'speech', 'ym', 'chain']:
    assert f'/api/{prefix}/*'.encode() in compose

web = inspect('ttd-stage', 'pymss-ui-preview-web')
image = ssh('ttd-stage', 'docker image inspect ' + shlex.quote('pymss-ui-preview:' + args.release)
            + ' --format ' + shlex.quote('{{.Id}}'))
assert web['Image'] == image and web['Config']['Labels']['ttd.preview.release'] == args.release
for path, expected in manifest['artifact'].items():
    data = urllib.request.urlopen('http://ttd-stage:17896/ui/' + path, timeout=20).read()
    assert sha(data) == expected, path

backend = inspect('ttd-stage', 'pymss-preview-runtime')
assert backend['Image'] == manifest['runtime_image']
assert backend['Config']['Labels']['ttd.preview.release'] == manifest['backend_release']
subnet = ssh('ttd-stage', 'docker network inspect pymss-ui-preview_default --format '
             + shlex.quote('{{range .IPAM.Config}}{{.Subnet}}{{end}}'))
assert subnet == '10.35.0.0/24'
previous = inspect('ttd-stage', 'audio-separation-entry')
assert previous['Config']['Labels']['ttd.audio.owner'] == 'pymss-webui'
assert previous['Config']['Labels']['ttd.audio.release'] == args.expected_current_release
previous_dir = previous['Config']['Labels']['com.docker.compose.project.working_dir']
assert previous_dir.startswith('/opt/audio-separation/releases/')

# Reconcile repository-owned snapshots, Compose management and effective runtime.
# These services remain running and shared: preview is not isolated from formal.
dependencies = {}
for key, host, name, checkout, commit, ready, url in [
    ('speech_backend', 'ttd-edge', 'clearvoice-audio-preview', root.parent / 'clearvoice-audio-api',
     args.speech_commit, 5, 'http://192.168.100.15:17902/api/speech/models'),
    ('ying_backend', 'ttd-edge', 'yingmusic-audio-preview', root.parent / 'yingmusic-audio-api',
     args.ying_commit, 1, 'http://192.168.100.15:17903/api/ym/models'),
    ('chain_backend', 'ttd-stage', 'pymss-chain-preview', root, args.source_commit, None, None),
]:
    expected = manifest[key]
    actual = inspect(host, name)
    assert actual['Image'] == expected['image'], name
    assert actual['State']['Status'] == 'running' and actual['State']['Health']['Status'] == 'healthy', name
    labels = actual['Config']['Labels']
    assert labels['ttd.preview.release'] == expected['release'], name
    management = f'/opt/{name}/releases/{expected["release"]}'
    assert labels['com.docker.compose.project.working_dir'] == management
    inputs = json.loads(ssh(host, 'cat ' + shlex.quote(management + '/input-manifest.json')))
    assert 'h-' + sha(json.dumps(inputs, sort_keys=True).encode())[:16] == expected['release']
    for path, digest in inputs.items():
        assert sha(source(checkout, commit, path)) == digest, f'{name}: {path}'
    deployed_compose = ssh(host, 'sha256sum ' + shlex.quote(management + '/compose.yaml')).split()[0]
    owned_compose = 'deploy/chain/compose.yaml' if key == 'chain_backend' else 'deploy/audio-preview/compose.yaml'
    assert deployed_compose == inputs[owned_compose]
    if url:
        models = get_json(url)['models']
        assert len(models) == ready and all(m['available'] for m in models), name
    dependencies[key] = dict(expected, host=host, container=name, container_id=actual['Id'],
                             source_commit=commit, management_dir=management,
                             verified_source_files=len(inputs), compose_sha256=deployed_compose,
                             mounts=[{k: m.get(k) for k in ('Source', 'Destination', 'RW')}
                                     for m in actual['Mounts'] if m['Type'] == 'bind'],
                             lifecycle='Existing managed shared dependency retained; no restart/admission/migration.')

promotion = dict(source_commit=args.source_commit, release=args.release, ui_image=image,
                 mode='prepared-not-deployed' if args.prepare else 'committed-preflight',
                 verified_ui_inputs=verified, compose_sha256=sha(compose),
                 dependencies=dependencies, backend_release=manifest['backend_release'],
                 backend_image=backend['Image'], backend_container_id=backend['Id'],
                 private_upstream='192.168.100.18:17898', private_origin='http://msst/ui/',
                 previous_image=previous['Image'], previous_management_dir=previous_dir,
                 rollback_command='cd ' + shlex.quote(previous_dir)
                                  + ' && docker compose --env-file .env -f compose.yaml up -d --no-build --pull never',
                 runtime_policy='CPU entry only. Preserve all shared providers, original MSST, portal, public ingress and NAS data.')
print(json.dumps(promotion, ensure_ascii=False, indent=2), flush=True)
if not args.apply:
    raise SystemExit(0)

# Recheck drift immediately before writes, after all read-only source checks.
assert inspect('ttd-stage', 'audio-separation-entry')['Id'] == previous['Id']
assert inspect('ttd-stage', 'pymss-preview-runtime')['Id'] == backend['Id']
for dependency in dependencies.values():
    current = inspect(dependency['host'], dependency['container'])
    assert current['Id'] == dependency['container_id'] and current['Image'] == dependency['image']
remote = f'/opt/audio-separation/releases/{args.release}-{args.source_commit[:12]}'
ssh('ttd-stage', 'mkdir -p ' + shlex.quote(remote))
with tempfile.TemporaryDirectory() as directory:
    folder = Path(directory)
    (folder / 'compose.yaml').write_bytes(compose)
    (folder / 'promotion-source.json').write_text(json.dumps(promotion, ensure_ascii=False, indent=2) + '\n')
    (folder / 'rollback.sh').write_text('#!/bin/sh\nset -eu\n' + promotion['rollback_command'] + '\n')
    (folder / '.env').write_text(f'AUDIO_UI_IMAGE={image}\nAUDIO_SOURCE_COMMIT={args.source_commit}\nAUDIO_RELEASE={args.release}\n')
    subprocess.run(['scp', '-q', *[str(folder / p) for p in ['compose.yaml', '.env', 'promotion-source.json', 'rollback.sh']],
                    'root@ttd-stage:' + remote + '/'], check=True)
subprocess.run(['ssh', '-o', 'BatchMode=yes', 'root@ttd-stage',
                shlex.join(['bash', '-s', '--', remote, previous['Id']])], input=r'''
set -euo pipefail
cd "$1"
test "$(docker inspect audio-separation-entry --format '{{.Id}}')" = "$2"
docker inspect audio-separation-entry > previous-container.json
ip route get 192.168.32.214 > home-route-before.txt
docker compose --env-file .env -f compose.yaml config --quiet
docker compose --env-file .env -f compose.yaml up -d --no-build --pull never
ip route get 192.168.32.214 > home-route-after.txt
''', text=True, check=True)

for _ in range(30):
    try:
        data = urllib.request.urlopen('http://msst/ui/', timeout=3).read()
        if sha(data) == manifest['artifact']['index.html']:
            break
    except Exception:
        pass
    time.sleep(2)
else:
    raise SystemExit('Formal UI differs from verified artifact; inspect private Caddy. No shared runtime was altered.')
assert b'window.gradio_config' in urllib.request.urlopen('http://msst/?native=msst', timeout=20).read()
for prefix, count in [('studio', 37), ('speech', 5), ('ym', 1)]:
    assert sum(m['available'] for m in get_json(f'http://msst/api/{prefix}/models')['models']) == count
assert inspect('ttd-stage', 'pymss-preview-runtime')['Id'] == backend['Id']
for dependency in dependencies.values():
    assert inspect(dependency['host'], dependency['container'])['Id'] == dependency['container_id']
print('Private entry promoted. Complete browser, chain, Range/ZIP and LAN/home acceptance; colleague listening remains NOT_RUN.')
