"""Promote the scoped Stage v2 consumer while preserving the existing Compose project."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import time

NAME = 'pymss-preview-runtime'
BASE_IMAGE = 'registry.ttd/pymss-webui/runtime@sha256:38fcad0bdf834a1d2ad22a34e9c87bb6e7bf00f75aa46c744527f23f7d7914e8'
BASE_SOURCE = '2005a0a50f9bfee9be1662addaaeffa4f891fa54'
CANDIDATE_IMAGE = 'registry.ttd/pymss-webui/runtime@sha256:9f4a545f89f243fbbec5cbed040b7ca05e761532553a6d3d2569f0f6be04b9b2'
CANDIDATE_SOURCE = 'b4b784108c433be6b30d9b8f68209858489e56ab'
NETWORK = 'pymss-ui-preview_default'


def run(*args, text=True):
    return subprocess.check_output(args, text=text)


def inspect(name):
    return json.loads(run('docker', 'inspect', name))[0]


def save(path, value):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def compose_command(labels):
    command = ['docker', 'compose']
    if labels.get('com.docker.compose.project.environment_file'):
        command += ['--env-file', labels['com.docker.compose.project.environment_file']]
    for path in labels['com.docker.compose.project.config_files'].split(','):
        command += ['-f', path]
    return command


def health():
    probe = "import json,urllib.request;print(json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:8000/healthz'))))"
    return json.loads(run('docker', 'exec', NAME, 'python', '-c', probe))


def verify(directory, plan):
    new = inspect(NAME)
    old = json.loads((directory / 'before.json').read_text())
    assert new['State']['Running'] and new['Config']['Image'] == plan['image']
    assert run('docker', 'exec', NAME, 'cat', '/opt/song-studio-source-commit').strip() == plan['source']
    assert new['HostConfig']['DeviceRequests'] == old['HostConfig']['DeviceRequests']
    assert new['HostConfig']['PortBindings'] == old['HostConfig']['PortBindings']
    assert all(m in new['Mounts'] for m in old['Mounts']) and len(new['Mounts']) == len(old['Mounts'])
    env = dict(item.split('=', 1) for item in new['Config']['Env'])
    assert env['STUDIO_GATEWAY_V2_SEPARATION'] == '1'
    assert env['NATIVE_GATEWAY_KEY_FILE'] == '/run/music-gateway.key'
    assert health()['status'] == 'ok'
    siblings = json.loads((directory / 'siblings.json').read_text())
    assert all(inspect(name)['Id'] == identity for name, identity in siblings.items())
    return {'image': plan['image'], 'source': plan['source'], 'container': new['Id'],
            'v2_enabled': True, 'mounts_ports_gpu_preserved': True, 'siblings_unchanged': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'apply', 'verify'])
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'registry\.ttd/pymss-webui/runtime@sha256:[a-f0-9]{64}', args.image)
    assert re.fullmatch(r'[a-f0-9]{40}', args.source)
    directory = args.directory.resolve()
    if args.phase == 'prepare':
        directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        old = inspect(NAME)
        assert old['State']['Running']
        source = run('docker', 'exec', NAME, 'cat', '/opt/song-studio-source-commit').strip()
        assert (old['Config']['Image'], source) in {(BASE_IMAGE, BASE_SOURCE), (CANDIDATE_IMAGE, CANDIDATE_SOURCE)}
        labels = old['Config']['Labels']
        assert labels['com.docker.compose.project'] == 'pymss-ui-preview'
        current = json.loads(run(*compose_command(labels), 'config', '--format', 'json'))
        runtime = current['services']['runtime']
        assert runtime['image'] == old['Config']['Image']
        actual_env = dict(item.split('=', 1) for item in old['Config']['Env'])
        assert all(actual_env.get(k) == str(v) for k, v in runtime['environment'].items())
        if source == CANDIDATE_SOURCE:
            assert actual_env.get('STUDIO_GATEWAY_V2_SEPARATION') == '1'
        else:
            assert actual_env.get('STUDIO_GATEWAY_V2_SEPARATION') != '1'
        siblings = run('docker', 'ps', '--filter', 'label=com.docker.compose.project=pymss-ui-preview',
                       '--format', '{{.Names}}').splitlines()
        sibling_ids = {name: inspect(name)['Id'] for name in siblings if name != NAME}
        subprocess.run(['docker', 'pull', args.image], check=True, stdout=subprocess.DEVNULL)
        source = run('docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'cat',
                     args.image, '/opt/song-studio-source-commit').strip()
        assert source == args.source
        target = copy.deepcopy(current)
        target['services'] = {'runtime': copy.deepcopy(runtime)}
        target['services']['runtime'].pop('depends_on', None)
        target['services']['runtime']['image'] = args.image
        target['services']['runtime']['environment']['STUDIO_GATEWAY_V2_SEPARATION'] = '1'
        target['services']['runtime'].setdefault('labels', {})['ttd.song.transport.source'] = source
        save(directory / 'before.json', old)
        save(directory / 'before-compose.json', current)
        save(directory / 'siblings.json', sibling_ids)
        save(directory / 'runtime-compose.json', target)
        save(directory / 'plan.json', {'image': args.image, 'source': source, 'old_id': old['Id'],
                                       'config_files': labels['com.docker.compose.project.config_files']})
        subprocess.run(['docker', 'compose', '--project-name', 'pymss-ui-preview', '-f',
                        str(directory / 'runtime-compose.json'), 'config', '--quiet'], check=True)
        print(json.dumps({'phase': 'prepared', 'source': source, 'image': args.image,
                          'changes': 'runtime image and STUDIO_GATEWAY_V2_SEPARATION only'}))
        return
    plan = json.loads((directory / 'plan.json').read_text())
    assert plan['image'] == args.image and plan['source'] == args.source
    if args.phase == 'verify':
        print(json.dumps(verify(directory, plan)))
        return
    assert not (directory / 'applied.json').exists()
    old = inspect(NAME)
    assert old['Id'] == plan['old_id'] and old['State']['Running']
    labels = old['Config']['Labels']
    assert labels['com.docker.compose.project.config_files'] == plan['config_files']
    assert json.loads(run(*compose_command(labels), 'config', '--format', 'json')) == json.loads((directory / 'before-compose.json').read_text())
    assert set(old['NetworkSettings']['Networks']) == {NETWORK}
    assert not health()['busy']
    subprocess.run(['docker', 'network', 'disconnect', NETWORK, NAME], check=True)
    deadline, idle_count = time.monotonic() + 1800, 0
    while idle_count < 3:
        state = health()
        processes = run('docker', 'top', NAME, '-eo', 'pid,ppid,stat,args')
        idle_count = idle_count + 1 if not state['busy'] and 'studio_runtime.worker' not in processes else 0
        if time.monotonic() > deadline:
            raise RuntimeError('Stage still busy; keep ingress fenced and inspect')
        time.sleep(2)
    subprocess.run(['docker', 'stop', '--timeout', '-1', NAME], check=True, stdout=subprocess.DEVNULL)
    command = ['docker', 'compose', '--project-name', 'pymss-ui-preview', '-f',
               str(directory / 'runtime-compose.json')]
    subprocess.run(command + ['up', '-d', '--no-build', '--no-deps', '--pull', 'never', 'runtime'], check=True)
    deadline = time.monotonic() + 90
    while True:
        try:
            receipt = verify(directory, plan)
            break
        except (AssertionError, subprocess.CalledProcessError, OSError):
            if time.monotonic() > deadline:
                raise RuntimeError('New Stage runtime did not become ready; inspect before rollback')
            time.sleep(2)
    save(directory / 'applied.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
