"""Scoped CPU song adapter; unrelated native DME execution is preserved."""
import json,os,sys
from pathlib import Path
from .native_worker import write, verification_key
from .managed_song import SONG_MODELS, run_song

def match_output_channels(path, source_channels):
    import soundfile as sf

    path=Path(path)
    state=json.loads(path.read_text())
    if state['status']!='succeeded':return
    for output in state['outputs']:
        if output['channels']==source_channels:continue
        target=path.parent/output['file']
        temporary=target.with_suffix('.channels.tmp')
        try:
            with sf.SoundFile(target) as original, sf.SoundFile(
                temporary, mode='w', samplerate=original.samplerate, channels=source_channels,
                format=original.format, subtype=original.subtype,
            ) as converted:
                for frames in original.blocks(blocksize=65536, dtype='float64', always_2d=True):
                    converted.write(frames.mean(axis=1) if source_channels==1 else frames.repeat(2,axis=1))
            temporary.replace(target)
            output['channels']=source_channels
        finally:
            temporary.unlink(missing_ok=True)
    write(path,state)

def run_short(path):
    import soundfile as sf

    state=json.loads(Path(path).read_text())
    source_channels=sf.info(state['input']).channels
    if state['model'] in SONG_MODELS:
        return run_song(path)

    from .native_worker import run as native
    path=Path(path)
    staged=path.with_name('native-job.json')
    write(path,dict(state,status='running',message='正在分离音轨…'))
    write(staged,state)
    native(staged)
    match_output_channels(staged,source_channels)
    staged.replace(path)


def run(path):
 state=json.loads(Path(path).read_text())
 if state.get('input_duration',0)>600:
  from .long_audio import run_long
  return run_long(path,run_short)
 return run_short(path)

if __name__=='__main__':
 import fcntl
 state=json.loads(Path(sys.argv[1]).read_text())
 if state['model'] in SONG_MODELS:run(sys.argv[1])
 else:
  # NFS implements shared flock as a read lock and needs a readable descriptor.
  with open('/data/gpu-worker.lock','a+') as lock:
   mode=fcntl.LOCK_SH if int(os.getenv('STUDIO_MAX_ACTIVE_JOBS','1'))>1 else fcntl.LOCK_EX
   fcntl.flock(lock,mode);run(sys.argv[1])
