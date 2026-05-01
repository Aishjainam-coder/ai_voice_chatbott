"""
lipsync.py — Natural Lip Sync (No Teeth, No Collapse)
====================================================
- Natural motion (no collapse)
- Teeth mostly hidden (not forced)
- Balanced jaw + lips
"""

import numpy as np
from scipy.io import wavfile

SILENCE_VISEME = "viseme_PP"


def extract_visemes(wav_path: str) -> list[dict]:
    try:
        sr, y = wavfile.read(wav_path)
    except Exception as e:
        print(f"[lipsync] Error reading wav: {e}")
        return []

    # Normalize
    if y.dtype != np.float32:
        y = y.astype(np.float32) / np.iinfo(y.dtype).max

    if len(y.shape) > 1:
        y = y.mean(axis=1)

    # Smooth audio
    y = np.convolve(y, np.ones(5)/5, mode='same')

    hop_length = 512
    n_frames = len(y) // hop_length
    frame_dur = hop_length / sr

    events = []

    for i in range(n_frames):
        t = i * frame_dur
        chunk = y[i * hop_length:(i + 1) * hop_length]

        if len(chunk) == 0:
            continue

        rms = np.sqrt(np.mean(chunk ** 2))

        if rms < 0.005:
            vis = SILENCE_VISEME
            jaw = 0.0
        else:
            vis = _pick_viseme_fast(rms)

            # ✅ Controlled jaw (natural)
            jaw = np.clip(rms * 2.0, 0.0, 0.28)

        # Base viseme
        events.append({
            "t": round(t, 4),
            "vis": vis,
            "dur": round(frame_dur, 4),
            "weight": round(float(jaw), 2)
        })

        if vis != SILENCE_VISEME:
            # ✅ Light lip control (NOT aggressive)
            lip_close = max(0.0, 0.3 - jaw)

            events.append({
                "t": round(t, 4),
                "vis": "jawOpen",
                "dur": round(frame_dur, 4),
                "weight": round(float(jaw), 2)
            })

            # Mild closing (prevents teeth but no collapse)
            events.append({
                "t": round(t, 4),
                "vis": "mouthClose",
                "dur": round(frame_dur, 4),
                "weight": round(float(lip_close), 2)
            })

            # Very subtle lip roll (optional realism)
            events.append({
                "t": round(t, 4),
                "vis": "mouthRollUpper",
                "dur": round(frame_dur, 4),
                "weight": round(float(lip_close * 0.3), 2)
            })

    events.sort(key=lambda e: e["t"])
    print(f"[lipsync] Done. {len(events)} events.")
    return events


def _pick_viseme_fast(rms: float) -> str:
    if rms < 0.01:
        return "viseme_PP"
    elif rms < 0.03:
        return "viseme_FF"
    else:
        return "viseme_aa"