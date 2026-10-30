"""Scoped CPU song adapter; unrelated native DME execution is preserved."""
import json,sys
from pathlib import Path
from .native_worker import write, verification_key
from .managed_song import SONG_MODELS, run_song

def run_short(path):
 state=json.loads(Path(path).read_text())
 if state['model'] in SONG_MODELS:return run_song(path)
 from .native_worker import run as native
 return native(path)

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
  with open('/data/gpu-worker.lock','a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);run(sys.argv[1])
