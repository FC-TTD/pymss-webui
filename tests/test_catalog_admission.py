import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('admission_prepare',Path(__file__).parents[1]/'deploy/catalog-admission/prepare.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class AdmissionTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'weights';self.root.mkdir();self.weight=self.root/'model.ckpt';self.weight.write_bytes(b'pinned-weights');self.config=self.root/'model.yaml';self.config.write_text('model: original\n');self.snapshot={'data':[{'id':'model.ckpt','pymss':{'model_type':'bs_roformer','category':'karaoke','target_stem':'vocals'}}]};self.hf={'id':'test/models','sha':'fixed','siblings':[]}
  for p in [self.weight,self.config]:
   b=p.read_bytes();row={'rfilename':p.name,'size':len(b),'blobId':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}
   if p.suffix=='.ckpt':row['lfs']={'sha256':hashlib.sha256(b).hexdigest()}
   self.hf['siblings'].append(row)
 def test_intact_pair_admitted_without_marking_available(self):
  out=module.prepare(self.snapshot,self.hf,self.root,{'models':[]});self.assertEqual(len(out['models']),1);self.assertNotIn('available',out['models'][0]);self.assertTrue(out['models'][0]['downloaded'])
 def test_corrupted_weight_is_rejected(self):
  self.weight.write_bytes(b'wrong-weights');out=module.prepare(self.snapshot,self.hf,self.root,{'models':[]});self.assertEqual(out['models'],[]);self.assertIn('权重',out['excluded'][0]['reason'])
 def test_registered_model_is_untouched(self):
  out=module.prepare(self.snapshot,self.hf,self.root,{'models':[{'id':'model.ckpt'}]});self.assertEqual(out['models'],[]);self.assertEqual(self.weight.read_bytes(),b'pinned-weights')
 def test_modified_local_config_is_rejected(self):
  self.config.write_text('model: modified\n');out=module.prepare(self.snapshot,self.hf,self.root,{'models':[]});self.assertEqual(out['models'],[]);self.assertIn('配置',out['excluded'][0]['reason'])
if __name__=='__main__':unittest.main()

spec_publish=importlib.util.spec_from_file_location('admission_publish',Path(__file__).parents[1]/'deploy/catalog-admission/promote.py');publisher=importlib.util.module_from_spec(spec_publish);spec_publish.loader.exec_module(publisher)
class PublishTest(unittest.TestCase):
 def test_missing_evidence_changes_nothing(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);m=r/'manifest.json';v=r/'verified.json';m.write_text('{"models":[]}');v.write_text('{}')
   with self.assertRaises(ValueError):publisher.publish(m,v,{'models':[{'id':'new'}]}, {},r/'backup')
   self.assertEqual(m.read_text(),'{"models":[]}');self.assertEqual(v.read_text(),'{}')
 def test_existing_records_and_requirements_survive(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);m=r/'manifest.json';v=r/'verified.json';q=r/'requirements.json';m.write_text('{"models":[{"id":"old","downloaded":true}]}');v.write_text('{"old":{"passed":true}}');q.write_text('{"old":100}')
   publisher.publish(m,v,{'models':[{'id':'old'},{'id':'new'}]},{'new':{'passed':True,'peak_cuda_bytes':200}},r/'backup',q)
   self.assertEqual(json.loads(v.read_text())['old'],{'passed':True});self.assertEqual(json.loads(q.read_text()),{'old':100,'new':200});self.assertEqual(len(json.loads(m.read_text())['models']),2)
