import asyncio,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from studio_runtime.resources import execute_with_capacity
from studio_runtime.managed_song import run_song
from studio_runtime.worker import verification_key

class SongBoundaryTests(unittest.TestCase):
 def test_song_launches_once_without_stage_gpu_probe_even_on_unknown(self):
  async def check():
   with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'job.json';path.write_text(json.dumps({'model':'bs_roformer_karaoke_anvuew.ckpt','status':'queued'}));calls=[]
    async def probe():self.fail('Stage GPU must not be probed for managed song')
    async def launch(path,log):calls.append(1);path.write_text(json.dumps({'model':'bs_roformer_karaoke_anvuew.ckpt','status':'unknown','error':'CUDA out of memory'}));return 1
    await execute_with_capacity(path,probe=probe,launch=launch,attempts=3)
    self.assertEqual(calls,[1]);self.assertEqual(json.loads(path.read_text())['status'],'unknown')
  asyncio.run(check())
 def test_prior_managed_attempt_is_never_replayed(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'job.json';p.write_text(json.dumps({'model':'bs_roformer_karaoke_anvuew.ckpt','managedAttempt':'existing','status':'running','outputs':[]}))
   with patch('studio_runtime.managed_song.requests.Session') as session:run_song(p)
   self.assertEqual(json.loads(p.read_text())['status'],'unknown');session.assert_not_called()
 def test_original_registry_verification_key_is_preserved(self):
  import hashlib
  from studio_runtime import native_worker
  model={'artifacts':[{'path':'unchanged','bytes':10}]}
  expected=hashlib.sha256((Path(native_worker.__file__).read_text()+json.dumps(model['artifacts'],sort_keys=True)+'pymss2.1.5-core0.1.8').encode()).hexdigest()
  self.assertEqual(verification_key(model),expected)

if __name__=='__main__':unittest.main()
