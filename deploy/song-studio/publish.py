"""Promote only the scoped studio runtime, keeping its API/data and other models."""
import json
import os
from pathlib import Path
import subprocess
import time

NAME = 'pymss-preview-runtime'
PREVIOUS = '8ff9aa4347f117d009df7ceaf46883f42965d2a0bc7fe2dafce1261ce10da638'
TARGET = 'registry.ttd/pymss-webui/runtime@sha256:e6488797b124593b70a020333b85a95f3cbcde00dccec5e76ec3f6af4660b7e8'


def save(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream, indent=2)


def inspect(name):
    return json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]


def main():
    root = Path('/opt/music-hub-release-20261027/studio-release')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    old = inspect(NAME)
    assert old['Id'] == PREVIOUS and old['State']['Running']
    assert not (root / 'before.json').exists(), 'Inspect an existing promotion before repeating it'
    labels = old['Config']['Labels']
    cmd = ['docker', 'compose', '--env-file', labels['com.docker.compose.project.environment_file'], '-f', labels['com.docker.compose.project.config_files']]
    desired = json.loads(subprocess.check_output(cmd + ['config', '--format', 'json']))
    runtime = desired['services']['runtime']
    assert runtime['image'] == old['Config']['Image']
    expected_env = {k: str(v) for k, v in runtime.get('environment', {}).items()}
    actual_env = dict(v.split('=', 1) for v in old['Config']['Env'])
    assert all(actual_env.get(k) == v for k, v in expected_env.items())
    save(root / 'before.json', old)
    save(root / 'before-compose.json', desired)
    siblings = subprocess.check_output(['docker', 'ps', '--filter', 'label=com.docker.compose.project=pymss-ui-preview', '--format', '{{.Names}}'], text=True).splitlines()
    before_ids = {name: inspect(name)['Id'] for name in siblings if name != NAME}
    save(root / 'siblings.json', before_ids)
    subprocess.run(['docker', 'pull', TARGET], check=True, stdout=subprocess.DEVNULL)
    proof = subprocess.check_output(['docker', 'run', '--rm', '--network', 'none', '--entrypoint', 'cat', TARGET, '/opt/song-studio-source-commit'], text=True).strip()
    assert proof == 'e6064fc03cb716319eab306ce62acf0b80c7509d'
    assert set(old['NetworkSettings']['Networks']) == {'pymss-ui-preview_default'}
    subprocess.run(['docker', 'network', 'disconnect', 'pymss-ui-preview_default', NAME], check=True)
    deadline, empty = time.monotonic() + 1800, 0
    probe = "import json,urllib.request;print(json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:8000/healthz'))))"
    while empty < 3:
        health = json.loads(subprocess.check_output(['docker', 'exec', NAME, 'python', '-c', probe]))
        top = subprocess.check_output(['docker', 'top', NAME, '-eo', 'pid,ppid,stat,args'], text=True)
        idle = not health['busy'] and 'studio_runtime.worker' not in top
        empty = empty + 1 if idle else 0
        if time.monotonic() > deadline:
            raise RuntimeError('Native studio still busy; preserve ingress fence without force kill')
        time.sleep(2)
    subprocess.run(['docker', 'stop', '--timeout', '-1', NAME], check=True, stdout=subprocess.DEVNULL)
    stopped = inspect(NAME)
    assert not stopped['State']['Running'] and not stopped['State']['OOMKilled']
    target = dict(desired)
    target['services'] = {'runtime': dict(runtime)}
    target['services']['runtime'].pop('depends_on', None)
    target['services']['runtime']['image'] = TARGET
    target['services']['runtime'].setdefault('labels', {}).update({'ttd.song.transport.source': proof, 'ttd.preview.release': 'h-fd9b69f2ce8a'})
    save(root / 'runtime-compose.json', target)
    command = ['docker', 'compose', '--project-name', 'pymss-ui-preview', '-f', str(root / 'runtime-compose.json')]
    subprocess.run(command + ['config', '--quiet'], check=True)
    subprocess.run(command + ['up', '-d', '--no-build', '--no-deps', '--pull', 'never', 'runtime'], check=True)
    new = inspect(NAME)
    assert new['Config']['Image'] == TARGET and new['Mounts'] == old['Mounts']
    assert new['HostConfig']['DeviceRequests'] == old['HostConfig']['DeviceRequests']
    assert new['HostConfig']['PortBindings'] == old['HostConfig']['PortBindings']
    deadline = time.monotonic() + 60
    while True:
        result = subprocess.run(['docker', 'exec', NAME, 'python', '-c', probe], capture_output=True)
        if not result.returncode and json.loads(result.stdout)['status'] == 'ok':
            break
        if time.monotonic() > deadline:
            raise RuntimeError('New CPU API did not become ready')
        time.sleep(1)
    assert all(inspect(name)['Id'] == identity for name, identity in before_ids.items())
    receipt = dict(image=TARGET, source=proof, container=new['Id'], native_old_exit=stopped['State']['ExitCode'],
        api_mounts_ports_preserved=True, unrelated_native_device_assignment_preserved=True, siblings_unchanged=True,
        song_execution='existing Hub-managed PYMSS native API')
    save(root / 'applied.json', receipt)
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
