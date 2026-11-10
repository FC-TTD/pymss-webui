import asyncio, importlib.util, json, subprocess, sys, types
from pathlib import Path
import numpy as np
import pytest
import soundfile as sf

ROOT=Path(__file__).resolve().parents[2]/'deploy/song-studio/runtime'
package=types.ModuleType('film_runtime');package.__path__=[str(ROOT)];sys.modules['film_runtime']=package
from film_runtime.media import probe, extract
from film_runtime.long_audio import run_long
from film_runtime.native_worker import write

def ffmpeg(*args):
    subprocess.run(['ffmpeg','-nostdin','-v','error',*map(str,args)],check=True)

def test_video_stream_selection_and_surround_center(tmp_path):
    video=tmp_path/'two-tracks.mkv'
    # Center-only dialogue must reach both channels; a second language differs.
    ffmpeg('-f','lavfi','-i','color=size=16x16:rate=1:duration=2','-f','lavfi','-i',
        'aevalsrc=0|0|0.2*sin(2*PI*440*t)|0|0|0:s=48000:d=2:c=5.1',
        '-f','lavfi','-i','sine=frequency=880:sample_rate=48000:duration=2',
        '-map','0:v','-map','1:a','-map','2:a','-metadata:s:a:0','language=zho',
        '-metadata:s:a:1','language=eng','-c:v','ffv1','-c:a','flac',video)
    streams=asyncio.run(probe(video))
    assert len(streams)==2 and streams[0]['channels']==6 and streams[1]['language']=='eng'
    first=tmp_path/'first.flac';second=tmp_path/'second.flac'
    asyncio.run(extract(video,first,streams[0]['index']));asyncio.run(extract(video,second,streams[1]['index']))
    a,sr=sf.read(first,always_2d=True);b,_=sf.read(second,always_2d=True)
    assert len(a)==96000 and a.shape[1]==2 and np.max(abs(a[:,0]))>.02
    assert np.max(abs(a[:,0]-a[:,1]))<1e-6
    assert b.shape==(96000,1) and not np.allclose(a[:,0],b[:,0])

def test_silent_video_is_rejected(tmp_path):
    video=tmp_path/'silent.mkv';ffmpeg('-f','lavfi','-i','color=size=16x16:rate=1:duration=1','-c:v','ffv1',video)
    with pytest.raises(Exception,match='没有可读取'):asyncio.run(probe(video))

@pytest.mark.parametrize('seconds',[17,16])
def test_window_join_retains_length_signal_and_stereo(tmp_path,seconds):
    rate=48000;frames=seconds*rate+137
    t=np.arange(frames)/rate;audio=np.stack([.1*np.sin(t*440*2*np.pi),.1*np.sin(t*880*2*np.pi)],axis=1)
    source=tmp_path/'source.flac';sf.write(source,audio,rate,subtype='PCM_24')
    path=tmp_path/'job.json';write(path,dict(id='a'*32,model='identity',input=str(source),stems=['Other'],status='queued',outputs=[]))
    lengths=[]
    def identity(child):
        state=json.loads(child.read_text());x,sr=sf.read(state['input'],always_2d=True);lengths.append(len(x)/sr)
        sf.write(child.parent/'other.wav',x,sr,subtype='PCM_24')
        state.update(status='succeeded',outputs=[dict(stem='Other',file='other.wav',sample_rate=sr,channels=2)]);write(child,state)
    run_long(path,identity,step=4)
    result=json.loads(path.read_text());assert result['status']=='succeeded',result
    out,_=sf.read(tmp_path/result['outputs'][0]['file'],always_2d=True)
    assert out.shape==audio.shape and len(lengths)==5 and max(lengths)<=8
    assert np.max(abs(out-audio))<5e-7

@pytest.mark.parametrize('layout,channel_count,signal_channel',[('5.1',6,3),('7.1',8,6)])
def test_downmix_retains_lfe_and_surround(tmp_path,layout,channel_count,signal_channel):
    source=tmp_path/'source.wav';expr=['0']*channel_count;expr[signal_channel]='0.2*sin(2*PI*100*t)'
    ffmpeg('-f','lavfi','-i','aevalsrc='+'|'.join(expr)+':s=48000:d=1:c='+layout,'-c:a','pcm_s24le',source)
    stream=asyncio.run(probe(source))[0];target=tmp_path/'out.flac'
    asyncio.run(extract(source,target,stream['index']))
    audio,_=sf.read(target,always_2d=True)
    assert audio.shape==(48000,2) and np.max(abs(audio))>.01


def test_uncertain_segment_is_not_replayed(tmp_path):
    source=tmp_path/'source.flac';sf.write(source,np.ones((6*48000,2))*.01,48000)
    path=tmp_path/'job.json';state=dict(id='b'*32,model='identity',input=str(source),stems=['Other'],status='queued',outputs=[]);write(path,state)
    folder=tmp_path/'segments/0';folder.mkdir(parents=True);write(folder/'job.json',dict(state,status='unknown',managedAttempt='previous'))
    called=[];run_long(path,lambda p:called.append(p),step=4)
    assert not called and json.loads(path.read_text())['status']=='unknown'


def test_long_audio_windows_reuse_canonical_asset_across_models(tmp_path):
    asset='a'*32
    canonical=tmp_path/asset;canonical.mkdir()
    source=canonical/'input.audio'
    sf.write(source,np.ones((9*48000,2))*.01,48000,format='FLAC',subtype='PCM_24')
    write(canonical/'job.json',dict(id=asset,model='first',input=str(source),input_asset_id=asset,stems=['Other'],status='queued',outputs=[]))
    def identity(child):
        state=json.loads(child.read_text());audio,rate=sf.read(state['input'],always_2d=True)
        sf.write(child.parent/'other.wav',audio,rate,subtype='PCM_24')
        state.update(status='succeeded',outputs=[dict(stem='Other',file='other.wav',sample_rate=rate,channels=2)]);write(child,state)
    run_long(canonical/'job.json',identity,step=4)
    second=tmp_path/('b'*32);second.mkdir()
    child_job=second/'job.json'
    write(child_job,dict(id='b'*32,model='second',input=str(source),input_asset_id=asset,stems=['Other'],status='queued',outputs=[]))
    run_long(child_job,identity,step=4)
    for number in range(3):
        shared=canonical/'segment-inputs'/str(number)/'input.flac'
        assert shared.is_file()
        assert shared.samefile(canonical/'segments'/str(number)/'input.flac')
        assert shared.samefile(second/'segments'/str(number)/'input.flac')
    assert json.loads(child_job.read_text())['status']=='succeeded'


def test_existing_ten_minute_inputs_keep_original_execution(tmp_path,monkeypatch):
    from film_runtime import worker,long_audio
    calls=[]
    monkeypatch.setattr(worker,'run_short',lambda path:calls.append('native'))
    monkeypatch.setattr(long_audio,'run_long',lambda path,execute:calls.append('windowed'))
    path=tmp_path/'job.json'
    path.write_text(json.dumps({'input_duration':600}));worker.run(path)
    path.write_text(json.dumps({'input_duration':601}));worker.run(path)
    assert calls==['native','windowed']

@pytest.mark.parametrize('rate,tail',[(44100,137),(192000,1)])
def test_subsecond_tail_with_resampling_is_complete(tmp_path,rate,tail):
    from math import gcd
    from scipy.signal import resample_poly
    frames=16*rate+tail;t=np.arange(frames)/rate
    source=tmp_path/'source.flac';sf.write(source,np.stack([.1*np.sin(t*440*2*np.pi)]*2,axis=1),rate,subtype='PCM_24')
    path=tmp_path/'job.json';write(path,dict(id='c'*32,model='identity',input=str(source),stems=['Other'],status='queued',outputs=[]))
    def resampling_identity(child):
        state=json.loads(child.read_text());audio,sr=sf.read(state['input'],always_2d=True)
        d=gcd(sr,48000);audio=resample_poly(audio,48000//d,sr//d,axis=0)
        sf.write(child.parent/'other.wav',audio,48000,subtype='PCM_24')
        state.update(status='succeeded',outputs=[dict(stem='Other',file='other.wav',sample_rate=48000,channels=2)]);write(child,state)
    run_long(path,resampling_identity,step=4)
    state=json.loads(path.read_text());assert state['status']=='succeeded',state
    output,_=sf.read(tmp_path/state['outputs'][0]['file'],always_2d=True)
    assert abs(len(output)-round(frames/rate*48000))<=1 and output.shape[1]==2
    assert np.isfinite(output).all() and np.max(abs(output))>.05


def test_tracks_use_audio_duration_instead_of_longer_video(tmp_path):
    video=tmp_path/'different-durations.mkv'
    ffmpeg('-f','lavfi','-i','color=size=16x16:rate=1:duration=3',
        '-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=1.2',
        '-f','lavfi','-i','sine=frequency=880:sample_rate=48000:duration=2.4',
        '-map','0:v','-map','1:a','-map','2:a','-c:v','ffv1','-c:a','flac',video)
    streams=asyncio.run(probe(video))
    assert abs(streams[0]['duration']-1.2)<.001 and abs(streams[1]['duration']-2.4)<.001


@pytest.mark.parametrize("input_channels,model_channels", [(1,2),(2,1),(2,2),(1,1)])
def test_export_matches_source_channels(tmp_path,input_channels,model_channels):
    from film_runtime.worker import match_output_channels

    target=tmp_path/'out.wav'
    audio=np.tile(np.arange(1,model_channels+1)*.1,(128,1))
    sf.write(target,audio,48000,subtype='PCM_24')
    path=tmp_path/'job.json'
    write(path,dict(status='succeeded',outputs=[dict(file=target.name,channels=model_channels)]))
    match_output_channels(path,input_channels)
    info=sf.info(target)
    assert (info.channels,info.frames,info.samplerate,info.subtype)==(input_channels,128,48000,'PCM_24')
    assert json.loads(path.read_text())['outputs'][0]['channels']==input_channels
    expected=audio if input_channels==model_channels else np.repeat(audio.mean(axis=1,keepdims=True),input_channels,axis=1)
    assert np.allclose(sf.read(target,always_2d=True)[0],expected,atol=3e-7)


def test_four_native_workers_overlap_when_memory_allows(tmp_path):
    from film_runtime.resources import execute_with_capacity

    async def exercise():
        all_started=asyncio.Event()
        active=set()
        async def probe():
            return 16000
        async def launch(path,log):
            active.add(path)
            if len(active)==4:
                all_started.set()
            await asyncio.wait_for(all_started.wait(),timeout=2)
            write(path,dict(model='test-model',status='succeeded'))
            return 0

        paths=[]
        for number in range(4):
            path=tmp_path/'jobs'/str(number)/'job.json'
            path.parent.mkdir(parents=True)
            write(path,dict(model='test-model',status='queued'))
            paths.append(path)
        await asyncio.gather(*(execute_with_capacity(p,probe=probe,launch=launch) for p in paths))
        assert active==set(paths)

    asyncio.run(exercise())


def test_four_batches_are_admitted_and_fifth_can_retry(tmp_path,monkeypatch):
    import httpx
    monkeypatch.setenv('STUDIO_JOBS',str(tmp_path/'jobs'))
    monkeypatch.setenv('STUDIO_MAX_ACTIVE_JOBS','4')
    from film_runtime import app as studio

    async def exercise():
        all_started=asyncio.Event()
        finish=asyncio.Event()
        active=set()
        async def run(path):
            active.add(path)
            if len(active)==4:
                all_started.set()
            await finish.wait()
            write(path,dict(json.loads(path.read_text()),status='succeeded'))
        monkeypatch.setattr(studio,'execute_with_capacity',run)
        monkeypatch.setattr(studio,'registry',lambda:[dict(id='fixture',available=True,stems=[dict(id='Other')])])
        fixture=tmp_path/'input.wav'
        sf.write(fixture,np.zeros(4800),48000)
        params={'model':'fixture','stems':'["Other"]'}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=studio.app),base_url='http://test') as client:
            batches=[]
            for _ in range(5):
                batch=await client.post('/api/studio/batches',params=params)
                assert batch.status_code==201,batch.text
                endpoint='/api/studio/batches/'+batch.json()['id']
                uploaded=await client.post(endpoint+'/inputs',params={'filename':'input.wav'},content=fixture.read_bytes())
                assert uploaded.status_code==201,uploaded.text
                batches.append(endpoint)
            try:
                responses=await asyncio.gather(*(client.post(b+'/start') for b in batches[:4]))
                assert [response.status_code for response in responses]==[202]*4
                await asyncio.wait_for(all_started.wait(),timeout=2)
                assert (await client.post(batches[4]+'/start')).status_code==429
            finally:
                finish.set()
                await asyncio.sleep(0)
            assert studio.active==0
            assert (await client.post(batches[4]+'/start')).status_code==202
            await asyncio.sleep(0)
            assert studio.active==0

    asyncio.run(exercise())


def test_slow_upload_only_blocks_its_own_batch(tmp_path):
    import uuid
    import httpx
    from fastapi import FastAPI
    from film_runtime.batch import install_batch_routes

    data = tmp_path / 'jobs'
    data.mkdir()
    app = FastAPI()
    jobs = {}
    processed = []
    upload_held = asyncio.Event()
    release_upload = asyncio.Event()

    async def store_input(request, model, filename, stems, purpose):
        if filename == 'slow.wav':
            upload_held.set()
        body = b''.join([chunk async for chunk in request.stream()])
        job_id = uuid.uuid4().hex
        folder = data / job_id
        folder.mkdir()
        (folder / 'input.audio').write_bytes(body)
        jobs[job_id] = {'id': job_id, 'status': 'queued'}
        return job_id

    async def execute(path, release_slot):
        processed.append(path.parent.name)
        jobs[path.parent.name]['status'] = 'succeeded'

    async def body_stream():
        yield b'first'
        await release_upload.wait()
        yield b'second'

    install_batch_routes(app, data, lambda *_: ['Other'], store_input, jobs.__getitem__,
                         jobs.__getitem__, execute, lambda: None, lambda: None)

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url='http://test') as client:
            async def create():
                batch = await client.post('/api/studio/batches', params={'model': 'fixture', 'stems': '["Other"]'})
                return '/api/studio/batches/' + batch.json()['id']

            first, second = await create(), await create()
            async def upload(route, name, content):
                return await client.post(route+'/inputs', params={'filename': name}, content=content)

            slow = asyncio.create_task(upload(first, 'slow.wav', body_stream()))
            await asyncio.wait_for(upload_held.wait(), timeout=2)
            same = asyncio.create_task(upload(first, 'same.wav', b'third'))
            try:
                other = await asyncio.wait_for(upload(second, 'fast.wav', b'other'), timeout=2)
                assert other.status_code == 201
                start = await asyncio.wait_for(client.post(second+'/start'), timeout=2)
                assert start.status_code == 202
                await asyncio.sleep(0)
                assert processed == [other.json()['jobs'][0]['id']]
                assert not slow.done() and not same.done()
            finally:
                release_upload.set()
                completed = await asyncio.gather(slow, same)
            assert [r.status_code for r in completed] == [201, 201]
            batch = (await client.get(first)).json()
            assert len(batch['jobs']) == 2
            assert batch['uploaded_bytes'] == len(b'firstsecondthird')

    asyncio.run(exercise())
