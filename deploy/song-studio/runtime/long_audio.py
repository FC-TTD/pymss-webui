"""Bounded audio windows, original execution paths, context and crossfaded joins."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import soundfile as sf
from .native_worker import write

STEP=240
CONTEXT=2
FADE=.5

def run_long(path,execute,step=STEP):
    path=Path(path);job=json.loads(path.read_text());started=time.time()
    info=sf.info(job['input']);rate=info.samplerate;total=info.frames
    count=(total+step*rate-1)//(step*rate);writers={};tails={};outputs=[]
    job.update(status='running',message='正在分段处理长音频',outputs=[]);write(path,job)
    try:
        with sf.SoundFile(job['input']) as source:
            for number,core in enumerate(range(0,total,step*rate)):
                end=min(core+step*rate,total)
                left=max(0,core-CONTEXT*rate);right=min(total,end+CONTEXT*rate)
                folder=path.parent/'segments'/str(number);folder.mkdir(parents=True,exist_ok=True)
                job.update(message=f'正在处理第 {number+1} / {count} 段',segment=number+1,segments=count);write(path,job)
                child_path=folder/'job.json'
                if child_path.exists():
                    previous=json.loads(child_path.read_text())
                    if previous.get('status')!='succeeded' or previous.get('model')!=job['model'] or previous.get('stems')!=job['stems']:
                        job.update(status='unknown')
                        raise RuntimeError('已有未完成的分段执行记录，需先核对，未自动重跑。')
                else:
                    source.seek(left);audio=source.read(right-left,dtype='float32',always_2d=True)
                    sf.write(folder/'input.flac',audio,rate,format='FLAC',subtype='PCM_24');del audio
                    child=dict(job,input=str(folder/'input.flac'),status='queued',outputs=[])
                    child.pop('managedAttempt',None)
                    write(child_path,child)
                    execute(child_path)
                job.update(message=f'已处理第 {number+1} / {count} 段',segment=number+1,segments=count);write(path,job)
                result=json.loads((folder/'job.json').read_text())
                if result['status']!='succeeded':
                    job.update(status=result['status'],error=result.get('error','长音频片段未完成'))
                    raise RuntimeError('分段未完成；已完成片段保留，未自动重复执行。')
                if {o['stem'] for o in result['outputs']}!=set(job['stems']):raise ValueError('分段输出轨道不完整')
                for row in result['outputs']:
                    stem=row['stem'];out_rate=row['sample_rate']
                    if out_rate!=48000:raise ValueError('输出采样率不一致')
                    start=round((core-left)/rate*out_rate)-(round(FADE*out_rate) if core else 0)
                    stop=round((end-left)/rate*out_rate)+(round(FADE*out_rate) if end<total else 0)
                    with sf.SoundFile(folder/row['file']) as audio_file:
                        if audio_file.frames < stop:raise ValueError('模型输出发生截断')
                        audio_file.seek(start);chunk=audio_file.read(stop-start,dtype='float32',always_2d=True)
                    if not np.isfinite(chunk).all():raise ValueError('输出包含无效采样')
                    if stem not in writers:
                        name=hashlib.sha256(stem.encode()).hexdigest()[:16]+'.wav'
                        # RF64 is selected before exceeding classic WAV's 4 GB ceiling.
                        fmt='RF64' if total/rate*out_rate*row['channels']*3>=4294960000 else 'WAV'
                        writers[stem]=sf.SoundFile(path.parent/name,'w',samplerate=out_rate,channels=row['channels'],format=fmt,subtype='PCM_24')
                        outputs.append(dict(row,file=name,frames=0))
                    writer=writers[stem]
                    if stem in tails:
                        tail=tails.pop(stem);length=len(tail)
                        weight=np.linspace(0,1,length,dtype='float32')[:,None]
                        writer.write(tail*(1-weight)+chunk[:length]*weight);chunk=chunk[length:]
                    if end<total:
                        overlap=round(2*FADE*out_rate);tails[stem]=chunk[-overlap:].copy();chunk=chunk[:-overlap]
                    writer.write(chunk)
                del chunk
        for row in outputs:
            writer=writers[row['stem']];row['frames']=writer.tell()
            if abs(row['frames']-round(total/rate*48000))>1:raise ValueError('拼接后的音轨长度不完整')
        job.update(status='succeeded',message='分离完成',outputs=outputs,seconds=round(time.time()-started,2))
    except Exception as exc:
        job.update(status=job['status'] if job['status'] in ('unknown','failed') else 'failed',error=str(exc),outputs=[])
    finally:
        for writer in writers.values():writer.close()
        write(path,job)
