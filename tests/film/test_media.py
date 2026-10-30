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
    assert np.max(abs(a[:,0]-a[:,1]))<1e-6 and not np.allclose(a,b)

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
