"""CPU music restoration using the pinned upstream Deshimmer DSP."""
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import soundfile as sf

from .native_worker import resample, write

MODEL_ID = 'deshimmer'
STEM = 'restored'
LABEL = '修复后音乐'
OUTPUT_RATE = 48000
WINDOW_SECONDS = 60


def enabled():
    return os.getenv('STUDIO_ENABLE_DESHIMMER') == '1'


def repair(audio, sample_rate):
    from deshimmer.core import Params, process_stft

    frames = max(1, round(len(audio) * OUTPUT_RATE / sample_rate))
    if sample_rate != OUTPUT_RATE:
        audio = resample(audio.T, sample_rate, OUTPUT_RATE).T[:frames]
    # STFT requires a full analysis frame, even for very short input.
    params = Params(
        start_hz=4200, end_hz=12500, mix=0.75, total_att_cap_db=8,
        deres=0.35, deq_start_hz=3000, deq_end_hz=12500,
        swish_repair=0.18, tonal_repair=0.0, enhance=False,
    )
    if len(audio) < params.n_fft:
        audio = np.pad(audio, ((0, params.n_fft - len(audio)), (0, 0)))
    repaired = np.asarray(process_stft(audio, OUTPUT_RATE, params)).reshape(-1, audio.shape[1])[:frames]
    if repaired.shape != (frames, audio.shape[1]) or not np.isfinite(repaired).all():
        raise ValueError('修复结果长度或采样异常。')
    peak = float(np.max(np.abs(repaired)))
    return repaired / peak * 0.999 if peak >= 1 else repaired


def run_window(path):
    state = json.loads(path.read_text())
    audio, rate = sf.read(state['input'], dtype='float32', always_2d=True)
    repaired = repair(audio, rate)
    name = hashlib.sha256(STEM.encode()).hexdigest()[:16] + '.wav'
    sf.write(path.parent / name, repaired, OUTPUT_RATE, subtype='PCM_24')
    output = dict(stem=STEM, label=LABEL, file=name, frames=len(repaired),
                  channels=repaired.shape[1], sample_rate=OUTPUT_RATE)
    write(path, dict(state, status='succeeded', message='音乐修复完成', outputs=[output]))


def run(path):
    path = Path(path)
    state = json.loads(path.read_text())
    write(path, dict(state, status='running', message='正在修复音乐伪影…', outputs=[]))
    try:
        if not enabled():
            raise ValueError('音乐伪影修复暂不可用。')
        if sf.info(state['input']).duration > WINDOW_SECONDS:
            from .long_audio import run_long

            run_long(path, run_window, step=WINDOW_SECONDS)
        else:
            run_window(path)
    except Exception:
        write(path, dict(state, status='failed', error='音乐伪影修复未完成，输入已保留。', outputs=[]))
        raise
