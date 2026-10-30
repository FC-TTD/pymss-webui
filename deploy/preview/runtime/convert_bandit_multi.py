"""Extract official Zenodo tensor state without changing model parameters."""
import hashlib,json
from pathlib import Path
import torch
from pymss.config import load_config
from pymss.utils import get_model_from_config
ROOT=Path('/mnt/TTD-Data/pymss-ui-preview/models/bandit-multi')
original=ROOT/'checkpoint-multi.original.ckpt'
assert hashlib.md5(original.read_bytes()).hexdigest()=='fea2868787551b0cff36cfcf7c3622a3'
checkpoint=torch.load(original,map_location='cpu',weights_only=False)
state=checkpoint['state_dict'];print('Original keys',list(state)[:3],flush=True)
config=Path('/mnt/TTD-Data/pymss-ui-preview/models/experimental_general/checkpoint-cmn_state_dict.yaml')
model,_=get_model_from_config('bandit_v2',str(config))
expected=model.state_dict();chosen=None
for prefix in ['', 'model.','module.','model.model.']:
 candidate={k.removeprefix(prefix):v for k,v in state.items() if k.startswith(prefix)}
 if set(candidate)==set(expected) and all(candidate[k].shape==expected[k].shape for k in expected):chosen=candidate;break
if chosen is None:raise ValueError('Official checkpoint tensor names/shapes do not match the reviewed64-band config')
model.load_state_dict(chosen,strict=True)
converted=ROOT/'bandit_v2_multi.ckpt';torch.save(chosen,converted)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
row={'id':'bandit_v2_multi.ckpt','type':'bandit_v2','downloaded':True,'artifacts':[{'path':str(converted),'bytes':converted.stat().st_size,'sha256':sha(converted),'source':'https://zenodo.org/records/12701995/files/checkpoint-multi.ckpt?download=1','original_md5':'fea2868787551b0cff36cfcf7c3622a3'},{'path':str(config),'bytes':config.stat().st_size,'sha256':sha(config),'source':'https://huggingface.co/baicai1145/pymss/resolve/f02318ef92c43472777ed7aeeded3d2b29a68b58/experimental_general/checkpoint-cmn_state_dict.yaml'}]}
path=Path('/mnt/TTD-Data/pymss-ui-preview/download-manifest.json');manifest=json.loads(path.read_text());manifest['models']=[m for m in manifest['models'] if m['id']!=row['id']]+[row];path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(ROOT/'conversion.json').write_text(json.dumps({'source_url':row['artifacts'][0]['source'],'original_md5':'fea2868787551b0cff36cfcf7c3622a3','source_model_revision':'d5563d9031e95fdaa3e5a73d5020b9a0df61adb6','matched_tensors':len(chosen),'prefix_removed':prefix,'converted_sha256':sha(converted),'strict_load':True},indent=2)+'\n')
print('Strict tensor match / saved',len(chosen),flush=True)
