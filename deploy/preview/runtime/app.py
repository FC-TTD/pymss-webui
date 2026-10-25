"""Isolated LAN preview API. No Hub selection, load, or catalog mutations."""
import asyncio,json,sys,uuid,hashlib,mimetypes
from pathlib import Path
from fastapi import FastAPI,HTTPException,Request,Query
from fastapi.responses import FileResponse
from .worker import write, verification_key
from .waveform import audio_peaks
from .batch import install_batch_routes, recover_batches
from .resources import execute_with_capacity

DATA=Path('/data/jobs');DATA.mkdir(parents=True,exist_ok=True)
MANIFEST=Path('/model-cache/download-manifest.json')
VERIFIED=Path('/data/verified-models.json')
active=False
app=FastAPI(title='PYMSS Stage Preview')

DUO_IDS={'becruily_deux.ckpt','bs_leap_xe_voc.ckpt','bs_leap_xe_inst.ckpt','bs_roformer_voc_hyperacev2.ckpt','bs_roformer_inst_hyperacev2.ckpt','BS-Roformer-Resurrection.ckpt','BS-Roformer-Resurrection-Inst.ckpt','mel_band_roformer_vocals_becruily.ckpt','mel_band_roformer_instrumental_becruily.ckpt','Kim_MelBandRoformer.ckpt','kimmel_unwa_ft2_bleedless.ckpt','model_bs_roformer_ep_368_sdr_12.9628.ckpt','melband_roformer_instvox_duality_v2.ckpt','mel_band_roformer_instrumental_bleedless_v2_gabox.ckpt','bs_roformer_vocals_gabox.ckpt'}
KARAOKE_IDS={'mel_band_roformer_karaoke_becruily.ckpt','bs_roformer_karaoke_anvuew.ckpt'}
def display_label(model,key,fallback,purpose=None):
 if model in {'speech_bs_roformer_AliceN_sdr_20.4440.ckpt','speech_mel_roformer_AliceN_sdr_16.5716.ckpt'}:return {'vocals':'对白','speech':'对白','dry':'对白','other':'其余声音'}.get(key.lower(),fallback)
 if purpose=='dme' and model in DUO_IDS and key.lower() in {'other','instrument','instrumental'}:return '其余声音'
 if model in DUO_IDS and key.lower() in {'other','instrument','instrumental'}:return '伴奏'
 if model in {'gilliaan_drumsV1.ckpt','becruily_guitar.ckpt','gilliaan_bowedstrings_bs_v1.ckpt','bs_mega_53stem_piano_mvsep.ckpt','bs_mega_53stem_bass_mvsep.ckpt'} and key.lower()=='other':return '其余声音'
 if model in KARAOKE_IDS:
  return {'vocals':'主唱目标','instrumental':'和声及其余声音'}.get(key.lower(),fallback)
 if model in {'HTDemucs4.th','HTDemucs4_6stems.th','BS-Roformer-SW.ckpt','mel_band_roformer_4stems_xl_ver1.ckpt'} and key.lower()=='other':return '其他乐器'
 return {'drums':'鼓组','bass':'贝斯','guitar':'吉他','piano':'钢琴','strings':'弦乐'}.get(key.lower(),fallback)

def registry():
 manifest=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {'models':[]}
 verified=json.loads(VERIFIED.read_text()) if VERIFIED.exists() else {}
 rows=[]
 for m in manifest['models']:
  v=verified.get(m['id'],{});v=v if v.get('verification_key')==verification_key(m) else {};art=m.get('artifacts',[])
  rows.append({'id':m['id'],'available':bool(v.get('passed') and m['downloaded']),'downloaded':m['downloaded'],'stems':[dict(o,label=display_label(m['id'],o['id'],o['label'])) for o in v.get('stems',[])],'size':art[0]['bytes'] if art else 0,'reason':'' if v.get('passed') else ('当前空闲显存不足' if 'out of memory' in v.get('reason','').lower() else '当前环境暂不兼容' if v.get('reason') else '') or ('安装中' if m['downloaded'] else '下载未完成')})
 return rows
@app.on_event('startup')
def recover_interrupted():
 for path in DATA.glob('*/job.json'):
  try:
   state=json.loads(path.read_text())
   if state.get('status') in {'queued','running','waiting'}:
    state.update(status='failed',error='服务重启，任务未完成。请重新提交。',outputs=[]);write(path,state)
  except (OSError,ValueError):pass
 recover_batches(DATA.parent)

@app.get('/healthz')
def health():return {'status':'ok','busy':active}
@app.get('/api/studio/models')
def models():return {'models':registry()}

async def execute(path,release_slot=True):
 global active
 try:
  await execute_with_capacity(path)
 finally:
  if release_slot:active=False
@app.post('/api/studio/jobs',status_code=202)
async def submit(request:Request,model:str,filename:str,stems:str,purpose:str="duo"):
 global active
 validate_selection(model,stems)
 if active:raise HTTPException(429,'服务正在处理一个任务，请完成后再提交。')
 active=True
 try:
  job_id=await store_input(request,model,filename,stems,purpose)
  asyncio.create_task(execute(DATA/job_id/'job.json'));return {'id':job_id}
 except BaseException:active=False;raise

def validate_selection(model,stems):
 row=next((m for m in registry() if m['id']==model),None)
 if not row or not row['available']:raise HTTPException(409,'模型尚未就绪，请选择标为可使用的模型。')
 try:selected=json.loads(stems)
 except ValueError:raise HTTPException(400,'请选择需要输出的音轨。')
 if not isinstance(selected,list) or not selected or any(s not in [x['id'] for x in row['stems']] for s in selected):raise HTTPException(400,'请选择模型支持的输出音轨。')
 return selected

async def store_input(request,model,filename,stems,purpose):
 selected=validate_selection(model,stems)
 job_id=uuid.uuid4().hex;folder=DATA/job_id;folder.mkdir();target=folder/'input.audio';size=0;digest=hashlib.sha256()
 try:
  with target.open('wb') as f:
   async for chunk in request.stream():
    size+=len(chunk)
    if size>512*1024*1024:raise HTTPException(413,'音频不能超过512 MB。')
    digest.update(chunk)
    f.write(chunk)
  import soundfile as sf
  try:info=sf.info(target)
  except Exception: # ffprobe handles mp3/m4a when soundfile cannot.
   try:
    probe=await asyncio.create_subprocess_exec('ffprobe','-v','error','-show_entries','format=duration','-of','json',str(target),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    raw,_=await probe.communicate();duration=float(json.loads(raw)['format']['duration'])
   except Exception:raise HTTPException(400,'无法读取这段音频，请换成WAV或MP3。')
  else:duration=info.duration
  if not 0<duration<=600:raise HTTPException(400,'音频长度应在10分钟以内。')
  path=folder/'job.json';write(path,{'id':job_id,'model':model,'filename':Path(filename).name,'purpose':purpose,'input':str(target),'input_asset_id':job_id,'input_bytes':size,'input_duration':duration,'input_sha256':digest.hexdigest(),'stems':selected,'status':'queued','outputs':[]})
  return job_id
 except BaseException:raise

def load_job(job_id):
 if len(job_id)!=32 or any(c not in '0123456789abcdef' for c in job_id):raise HTTPException(404,'任务不存在。')
 path=DATA/job_id/'job.json'
 if not path.exists():raise HTTPException(404,'任务不存在。')
 return json.loads(path.read_text())

def load_asset(asset_id):
 source=load_job(asset_id)
 canonical=source.get('input_asset_id') or asset_id
 original=load_job(canonical)
 path=DATA/canonical/'input.audio'
 if not path.is_file() or not path.resolve().is_relative_to(DATA.resolve()):raise HTTPException(404,'已上传音频不存在，请重新选择文件。')
 return canonical,original,path

def reuse_input(asset_id,model,stems,purpose):
 selected=validate_selection(model,json.dumps(stems));canonical,source,path=load_asset(asset_id)
 job_id=uuid.uuid4().hex;folder=DATA/job_id;folder.mkdir()
 # Source audio is immutable. Reference its canonical server file; never copy/re-upload it.
 write(folder/'job.json',{'id':job_id,'model':model,'filename':source['filename'],'purpose':purpose,'input':str(path),'input_asset_id':canonical,'input_bytes':path.stat().st_size,'input_duration':source.get('input_duration',0),'input_sha256':source.get('input_sha256',''),'stems':selected,'status':'queued','outputs':[]})
 return job_id

@app.get('/api/studio/assets/{asset_id}/audio')
def input_audio(asset_id:str):
 _,source,path=load_asset(asset_id)
 return FileResponse(path,media_type=mimetypes.guess_type(source['filename'])[0] or 'application/octet-stream')
@app.get('/api/studio/jobs/{job_id}')
def job(job_id:str):
 state=load_job(job_id)
 if state.get('status')=='failed' and 'out of memory' in state.get('error','').lower():state['error']='此任务加载时显卡被其他任务占用；音频已保留，可继续未完成文件。'
 outputs=[]
 for output in state['outputs']:
  url=f'/api/studio/jobs/{job_id}/files/{output["file"]}'
  outputs.append({k:v for k,v in output.items() if k!='file'} | {'label':display_label(state['model'],output['stem'],output['label'],state.get('purpose')),'url':url,'waveform_url':url+'/waveform','bytes':(DATA/job_id/output['file']).stat().st_size})
 extra={}
 try:
  canonical,source,input_path=load_asset(job_id)
  duration=source.get('input_duration') or (outputs[0]['frames']/outputs[0]['sample_rate'] if outputs else 0)
  extra={'input_asset_id':canonical,'input_bytes':input_path.stat().st_size,'input_duration':duration,'input_url':f'/api/studio/assets/{canonical}/audio'}
 except HTTPException:pass
 return {k:v for k,v in state.items() if k not in {'input','outputs','attempt_log','required_gpu_mb','free_gpu_mb'}} | {'outputs':outputs} | extra

@app.get('/api/studio/jobs/{job_id}/files/{name}')
def file(job_id:str,name:str,download:bool=False):
 state=load_job(job_id)
 if state['status']!='succeeded' or name not in [o['file'] for o in state['outputs']]:raise HTTPException(404,'文件不存在。')
 output=next(o for o in state['outputs'] if o['file']==name)
 filename=Path(state['filename']).stem+'-'+display_label(state['model'],output['stem'],output['label'],state.get('purpose'))+'.wav' if download else None
 return FileResponse(DATA/job_id/name,media_type='audio/wav',filename=filename)

@app.get('/api/studio/jobs/{job_id}/files/{name}/waveform')
def waveform(job_id:str,name:str,bins:int=Query(900,ge=128,le=4096)):
 state=load_job(job_id)
 if state['status']!='succeeded' or name not in [o['file'] for o in state['outputs']]:raise HTTPException(404,'文件不存在。')
 return audio_peaks(DATA/job_id/name,bins)

def claim_slot():
 global active
 if active:raise HTTPException(429,'服务正在处理其他任务，请稍后开始本批次。')
 active=True
def release_slot():
 global active
 active=False

install_batch_routes(app,DATA,validate_selection,store_input,load_job,job,execute,claim_slot,release_slot,reuse_input)
