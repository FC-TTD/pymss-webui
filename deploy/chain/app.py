"""Server-side result reuse for PYMSS consumers; never loads a model or arbitrary URL."""
import hashlib,json,os,re,threading,uuid
from pathlib import Path
import requests
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,StrictStr
DATA=Path(os.environ.get('CHAIN_DATA','/data'));DATA.mkdir(parents=True,exist_ok=True)
PN='http://192.168.100.18:17896/api/studio'
CV='http://192.168.100.15:17902/api/speech'
YM='http://192.168.100.15:17903/api/ym'
app=FastAPI(title='PYMSS Derived Audio Assets');lock=threading.Lock()
MAX_BYTES=512*1024**2
class Selection(BaseModel):
 job_id:StrictStr
 stem:StrictStr

def write(path,value):
 temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
def api(url,method='get',**kwargs):
 try:
  r=requests.request(method,url,timeout=(8,900),**kwargs)
  if r.status_code>=400:raise HTTPException(503,'输入服务暂不可用，原结果已保留，请稍后重试。')
  return r.json()
 except requests.RequestException:raise HTTPException(503,'连接暂时中断，原结果已保留，请稍后重试。')
def provider(identity):
 if not re.fullmatch(r'(?:cv-|ym-)?[a-f0-9]{32}',identity):raise HTTPException(404,'结果不存在。')
 return CV if identity.startswith('cv-') else YM if identity.startswith('ym-') else PN

def origin_path(asset):return DATA/('asset-'+asset+'.json')
def public_record(state):
 return dict(pool_batch=state['pool_batch'],asset_id=state['asset_id'],filename=state['filename'],bytes=state['bytes'],duration=state['duration'],input_url='/api/studio/assets/'+state['asset_id']+'/audio',parent=state['parent'],sha256=state['sha256'])
@app.get('/healthz')
def health():return dict(status='ok',busy=lock.locked())
@app.get('/api/chain/assets/{asset}')
def asset_origin(asset:str):
 if not re.fullmatch('[a-f0-9]{32}',asset):raise HTTPException(404,'输入不存在。')
 p=origin_path(asset)
 if not p.is_file():raise HTTPException(404,'此音频没有上一轮处理记录。')
 return public_record(json.loads(p.read_text()))
@app.post('/api/chain/inputs',status_code=201)
def derive(selection:Selection):
 with lock:
  base=provider(selection.job_id);job=api(base+'/jobs/'+selection.job_id)
  if job.get('status')!='succeeded':raise HTTPException(409,'音轨尚未处理完成。')
  output=next((o for o in job.get('outputs',[]) if o.get('stem')==selection.stem),None)
  if not output:raise HTTPException(404,'音轨不存在。')
  prefix=base.rsplit('/api/',1)[1]
  allowed=r'/api/'+re.escape(prefix)+r'/jobs/'+re.escape(selection.job_id)+r'/files/[a-f0-9]{16}\.wav'
  if not re.fullmatch(allowed,output.get('url','')):raise HTTPException(400,'音轨地址无效。')
  if output.get('bytes',MAX_BYTES+1)>MAX_BYTES:raise HTTPException(413,'音轨超过512 MB，请先选取较短素材。')
  if output.get('frames',0)/max(1,output.get('sample_rate',1))>600:raise HTTPException(413,'音轨超过10分钟，请先选取较短素材。')
  key=hashlib.sha256((selection.job_id+'|'+selection.stem+'|'+str(output.get('bytes'))).encode()).hexdigest()
  path=DATA/(key+'.json');state=json.loads(path.read_text()) if path.exists() else {}
  if state.get('asset_id'):
   api(PN+'/jobs/'+state['asset_id']);return public_record(state)
  title=Path(job['filename']).stem;label=output.get('label',selection.stem)
  if job.get('purpose')=='dme':
   if selection.stem.lower() in ['instrumental','other','instrument']:label='国际声'
   elif selection.stem.lower() in ['vocals','vocal','speech']:label='人声（对白）'
  filename=re.sub(r'[\x00-\x1f/\\:*?"<>|]','_',title+'-'+label)[:160]+'.wav'
  parent=dict(job_id=selection.job_id,model=job['model'],stem=selection.stem,label=label,filename=job['filename'])
  # Persist pool identity before transfer. After a lost reply/restart inspect its
  # validated jobs instead of importing the result a second time.
  if not state.get('pool_batch'):
   b=api(PN+'/batches','post',params=dict(model='melband_roformer_instvox_duality_v2.ckpt',stems='["Vocals","Instrumental"]',purpose='duo'))
   state=dict(pool_batch=b['id'],parent=parent,filename=filename);write(path,state)
  b=api(PN+'/batches/'+state['pool_batch'])
  complete=next((j for j in b['jobs'] if j.get('input_asset_id') and j.get('input_sha256') and j.get('input_duration',0)>0),None)
  if complete is None:
   host=base.split('/api/',1)[0];url=host+output['url']
   with requests.get(url,stream=True,timeout=(8,60)) as source:
    source.raise_for_status();expected=int(source.headers.get('Content-Length','0'))
    if not 0<expected<=MAX_BYTES:raise HTTPException(413,'无法确认音轨大小，原结果已保留。')
    count=0;digest=hashlib.sha256()
    def chunks():
     nonlocal count
     for chunk in source.iter_content(1024*1024):
      count+=len(chunk)
      if count>expected or count>MAX_BYTES:raise ValueError('源音轨长度不一致')
      digest.update(chunk);yield chunk
     if count!=expected:raise ValueError('源音轨传输不完整')
    class Body:
     def __len__(self):return expected
     def __iter__(self):return chunks()
    b=api(PN+'/batches/'+state['pool_batch']+'/inputs','post',params=dict(filename=filename),headers={'Content-Type':'application/octet-stream'},data=Body())
   complete=b['jobs'][-1]
   if complete.get('input_sha256')!=digest.hexdigest():raise HTTPException(502,'音轨传输校验未通过，原结果已保留。')
  state.update(asset_id=complete['input_asset_id'],bytes=complete['input_bytes'],duration=complete['input_duration'],sha256=complete['input_sha256'])
  write(path,state);write(origin_path(state['asset_id']),state)
  return public_record(state)
