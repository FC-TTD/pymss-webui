import hashlib
import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path

import numpy as np
import requests
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]/'deploy/song-studio/runtime'
package=types.ModuleType('film_runtime');package.__path__=[str(ROOT)];sys.modules['film_runtime']=package
from film_runtime import gateway_v2
from film_runtime.resources import execute_with_capacity
from film_runtime.native_worker import write

class Response:
    def __init__(self,status,payload=None,content=b'',headers=None):
        self.status_code=status;self.payload=payload;self.content=content;self.headers=headers or {}
    def json(self):return self.payload
    def __enter__(self):return self
    def __exit__(self,*_):return False
    def iter_content(self,size):
        for index in range(0,len(self.content),size):yield self.content[index:index+size]

def test_gateway_v2_lost_submit_response_recovers_same_task(tmp_path,monkeypatch):
    asset='a'*32;folder=tmp_path/asset;folder.mkdir()
    source=folder/'input.audio'
    sf.write(source,np.ones((48000,2))*.05,48000,format='WAV',subtype='PCM_24')
    job=folder/'job.json'
    write(job,dict(id=asset,model='melband_roformer_instvox_duality_v2.ckpt',input_asset_id=asset,input=str(source),stems=['Vocals','Instrumental'],status='queued',outputs=[]))
    key_file=tmp_path/'key';key_file.write_text('private-key')
    monkeypatch.setenv('NATIVE_GATEWAY_KEY_FILE',str(key_file))
    monkeypatch.setenv('STUDIO_GATEWAY_V2_SEPARATION','1')
    audio=folder/'artifact.wav';sf.write(audio,np.ones((48000,2))*.02,48000,subtype='PCM_24')
    content=audio.read_bytes();digest=hashlib.sha256(content).hexdigest()
    artifacts=[dict(id=role+'-id',role=role,size_bytes=len(content),sha256=digest,sample_rate=48000,bits_per_sample=24) for role in ('vocals','instrumental')]
    task=dict(id='task-1',profile_id='dialogue-vocal',profile_version=gateway_v2.VERSION,state='succeeded',inputs=[dict(state='succeeded',artifacts=artifacts)])
    class Session:
        submit_calls=0
        status_calls=0
        keys=[]
        def __init__(self):self.headers={};self.trust_env=True
        def post(self,url,**kwargs):
            if url.endswith('/inputs/stage'):
                return Response(201 if self.submit_calls==0 else 200,dict(id='stage-'+asset,file_ref='file:stage-'+asset,input_hash='digest'))
            self.__class__.submit_calls+=1
            self.__class__.keys.append(kwargs['headers']['Idempotency-Key'])
            if self.submit_calls==1:raise requests.Timeout('response lost after acceptance')
            return Response(202,task)
        def get(self,url,**kwargs):
            if '/artifacts/' in url:return Response(200,content=content)
            self.__class__.status_calls+=1
            if self.status_calls==1:raise requests.Timeout('status response lost')
            return Response(200,task)
        def close(self):pass
    monkeypatch.setattr(gateway_v2.requests,'Session',Session)
    gateway_v2.run(job)
    interrupted=json.loads(job.read_text())
    assert interrupted['status']=='unknown' and interrupted['gatewayV2Key']=='stage-'+asset+'-whole'
    assert 'gatewayV2Task' not in interrupted
    gateway_v2.run(job)
    accepted=json.loads(job.read_text())
    assert accepted['status']=='unknown' and accepted['gatewayV2Task']=='task-1'
    gateway_v2.run(job)
    restored=json.loads(job.read_text())
    assert restored['status']=='succeeded' and restored['gatewayV2Task']=='task-1'
    assert len(restored['outputs'])==2 and all(row['frames']==48000 for row in restored['outputs'])
    assert Session.keys==['stage-'+asset+'-whole']*2
    assert Session.submit_calls==2

def test_gateway_v2_busy_retries_same_key_without_losing_job(tmp_path,monkeypatch):
    asset='b'*32;folder=tmp_path/asset;folder.mkdir()
    source=folder/'input.audio'
    sf.write(source,np.ones((48000,2))*.05,48000,format='WAV',subtype='PCM_24')
    job=folder/'job.json'
    write(job,dict(id=asset,model='becruily_deux.ckpt',input_asset_id=asset,input=str(source),stems=['Vocals','Instrumental'],status='queued',outputs=[]))
    key_file=tmp_path/'key';key_file.write_text('private-key')
    monkeypatch.setenv('NATIVE_GATEWAY_KEY_FILE',str(key_file))
    monkeypatch.setattr(gateway_v2.time,'sleep',lambda _:None)
    audio=folder/'artifact.wav';sf.write(audio,np.ones((48000,2))*.02,48000,subtype='PCM_24')
    content=audio.read_bytes();digest=hashlib.sha256(content).hexdigest()
    artifacts=[dict(id=role+'-id',role=role,size_bytes=len(content),sha256=digest,sample_rate=48000,bits_per_sample=24) for role in ('dialogue','background')]
    rejected=dict(id='task-rejected',profile_id='film-dialogue-deux',profile_version=gateway_v2.VERSION,state='failed',error='separation execution failed')
    task=dict(id='task-busy-retry',profile_id='film-dialogue-deux',profile_version=gateway_v2.VERSION,state='succeeded',inputs=[dict(state='succeeded',artifacts=artifacts)])
    class Session:
        keys=[]
        def __init__(self):self.headers={};self.trust_env=True
        def post(self,url,**kwargs):
            if url.endswith('/inputs/stage'):
                return Response(201,dict(id='stage-'+asset,file_ref='file:stage-'+asset,input_hash='digest'))
            self.__class__.keys.append(kwargs['headers']['Idempotency-Key'])
            if len(self.keys)==1:return Response(429,headers={'Retry-After':'1'})
            waiting=json.loads(job.read_text())
            if len(self.keys)==2:
                assert waiting['status']=='waiting' and waiting['gatewayV2Retries']==1
                return Response(202,rejected)
            assert waiting['status']=='waiting' and waiting['gatewayV2Attempt']==1
            assert waiting['gatewayV2ResumeFrom']=='task-rejected'
            assert kwargs['json']['resume_from']=='task-rejected'
            return Response(202,task)
        def get(self,url,**kwargs):
            return Response(200,content=content) if '/artifacts/' in url else Response(200,task)
        def close(self):pass
    monkeypatch.setattr(gateway_v2.requests,'Session',Session)
    gateway_v2.run(job)
    restored=json.loads(job.read_text())
    assert restored['status']=='succeeded' and restored['gatewayV2Task']=='task-busy-retry'
    assert len(restored['outputs'])==2 and restored['gatewayV2Retries']==1
    assert Session.keys==['stage-'+asset+'-whole']*2+['stage-'+asset+'-whole-retry-1']

def test_v2_transport_retry_keeps_persisted_key_and_skips_stage_gpu(tmp_path,monkeypatch):
    monkeypatch.setenv('STUDIO_GATEWAY_V2_SEPARATION','1')
    path=tmp_path/'job.json'
    write(path,dict(model='becruily_deux.ckpt',status='queued',gatewayV2Key='stage-'+'b'*32+'-whole'))
    calls=[]
    async def probe():raise AssertionError('Stage GPU must not be probed for Gateway v2')
    async def launch(path,log):
        calls.append(1)
        state=json.loads(path.read_text())
        state['status']='unknown' if len(calls)==1 else 'succeeded'
        write(path,state)
        return 0
    asyncio.run(execute_with_capacity(path,probe=probe,launch=launch))
    assert calls==[1,1]
    assert json.loads(path.read_text())['gatewayV2Key']=='stage-'+'b'*32+'-whole'

def test_startup_resumes_only_unbatched_v2_jobs_with_durable_keys(tmp_path,monkeypatch):
    monkeypatch.setenv('STUDIO_GATEWAY_V2_SEPARATION','1')
    monkeypatch.setenv('STUDIO_JOBS',str(tmp_path/'jobs'))
    spec=importlib.util.spec_from_file_location('film_runtime.recovery_test_app',ROOT/'app.py')
    stage_app=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage_app)
    jobs=tmp_path/'jobs';jobs.mkdir(exist_ok=True)
    monkeypatch.setattr(stage_app,'DATA',jobs)
    single='a'*32;batched='b'*32
    for job_id in (single,batched):
        folder=jobs/job_id;folder.mkdir()
        write(folder/'job.json',dict(id=job_id,model='becruily_deux.ckpt',status='running',gatewayV2Key='stage-'+job_id+'-whole'))
    batch=tmp_path/'batches'/('c'*32);batch.mkdir(parents=True)
    write(batch/'batch.json',dict(id='c'*32,status='running',jobs=[batched]))
    resumed=[]
    async def fake_resume(path):resumed.append(path.parent.name)
    monkeypatch.setattr(stage_app,'resume_v2',fake_resume)
    async def check():
        stage_app.recover_interrupted()
        await asyncio.sleep(0)
    asyncio.run(check())
    assert resumed==[single]
    assert all(json.loads((jobs/job_id/'job.json').read_text())['status']=='queued' for job_id in (single,batched))
    assert json.loads((batch/'batch.json').read_text())['status']=='interrupted'
