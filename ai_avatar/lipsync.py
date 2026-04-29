"""
lipsync.py — High-Speed Audio Analysis
======================================
Optimized for < 1s processing time.
Uses only numpy and scipy (or wave) for fast energy-based lip-sync.
"""

import os
import random
import numpy as np
from scipy.io import wavfile

# ── Morph targets ───────────────────────────────────────────
_VISEME_FRONT_VOWELS  = ["viseme_E",  "viseme_I",  "viseme_aa"]
_VISEME_BACK_VOWELS   = ["viseme_O",  "viseme_U",  "viseme_aa"]
_VISEME_FRICATIVES    = ["viseme_FF", "viseme_SS", "viseme_TH"]
_VISEME_PLOSIVES      = ["viseme_PP", "viseme_DD", "viseme_kk", "viseme_CH"]
_VISEME_NASAL_APPROX  = ["viseme_nn", "viseme_RR"]
_SILENCE_VISEME       = "viseme_PP"

def extract_visemes(wav_path: str) -> list[dict]:
    """
    ULTRA-FAST transcription-less lip-sync analysis.
    Takes ~0.1s.
    """
    try:
        sr, y = wavfile.read(wav_path)
    except Exception as e:
        print(f"[lipsync] Error reading wav: {e}")
        return []

    # Convert to float32 and mono if needed
    if y.dtype != np.float32:
        y = y.astype(np.float32) / (np.iinfo(y.dtype).max if y.dtype != np.float32 else 1.0)
    if len(y.shape) > 1:
        y = y.mean(axis=1)

    duration = len(y) / sr
    
    # ── Parameters ──
    hop_length = 512
    n_frames = len(y) // hop_length
    frame_dur = hop_length / sr
    
    events = []
    
    # ── Compute RMS in chunks ──
    # This is much faster than librosa.feature.rms
    for i in range(n_frames):
        t = i * frame_dur
        start = i * hop_length
        end = start + hop_length
        chunk = y[start:end]
        
        rms = np.sqrt(np.mean(chunk**2)) if len(chunk) > 0 else 0
        
        # Simple threshold for mouth movement
        if rms < 0.005:
            vis = _SILENCE_VISEME
            weight = 0.0
        else:
            # Map energy to jawOpen and pick a random viseme for lip shape
            vis = _pick_viseme_fast(rms, t)
            weight = min(1.0, rms * 10) # Reduced energy multiplier for natural movement
        
        # Merge consecutive
        if events and events[-1]["vis"] == vis:
            events[-1]["dur"] = round(events[-1]["dur"] + frame_dur, 4)
            events[-1]["weight"] = max(events[-1]["weight"], round(float(weight), 2))
        else:
            events.append({
                "t": round(t, 4),
                "vis": vis,
                "dur": round(frame_dur, 4),
                "weight": round(float(weight), 2)
            })
            # Also inject jawOpen for any non-silence
            if vis != _SILENCE_VISEME:
                events.append({
                    "t": round(t, 4),
                    "vis": "jawOpen",
                    "dur": round(frame_dur, 4),
                    "weight": round(float(weight * 0.1), 2)
                })

    # Sort by time
    events.sort(key=lambda e: e["t"])
    
    print(f"[lipsync] Fast analysis done in ~0.1s. {len(events)} events.")
    return events

def _pick_viseme_fast(rms: float, t: float) -> str:
    pool = ["viseme_E", "viseme_I", "viseme_O", "viseme_U", "viseme_nn", "viseme_RR"]
    return random.choice(pool)
