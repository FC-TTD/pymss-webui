"""Small, real PCM peak envelopes. Never decode an entire song in the browser."""
import json,os,tempfile
from pathlib import Path
import numpy as np
import soundfile as sf


def audio_peaks(path:Path,bins:int=900):
    stat=path.stat();identity=f'{stat.st_size}:{stat.st_mtime_ns}'
    cache=path.with_name(path.name+f'.waveform-v1-{bins}.json')
    try:
        data=json.loads(cache.read_text())
        if data.get('identity')==identity:return data
    except (OSError,ValueError):pass
    peaks=[]
    with sf.SoundFile(path) as audio:
        frames=len(audio);rate=audio.samplerate;channels=audio.channels
        count=min(bins,max(1,frames))
        # Exact bins, constant memory; stereo takes the largest channel magnitude.
        for i in range(count):
            length=(i+1)*frames//count-i*frames//count
            block=audio.read(length,dtype='float32',always_2d=True)
            peaks.append(round(float(np.max(np.abs(block))) if block.size else 0.,6))
    data={'version':1,'identity':identity,'frames':frames,'sample_rate':rate,'channels':channels,'duration':frames/rate,'peaks':peaks}
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,suffix='.waveform.tmp',delete=False) as f:
            temporary=Path(f.name);json.dump(data,f,separators=(',',':'))
        os.replace(temporary,cache)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    return data
