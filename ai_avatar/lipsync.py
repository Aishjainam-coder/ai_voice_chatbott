"""
lipsync.py — Audio WAV → Viseme Timestamps JSON
================================================
Responsibilities:
  - Load a .wav file with librosa
  - Extract amplitude-based frame energies
  - Map energy levels to viseme shapes
  - Produce a time-stamped list of viseme events:
      [{t: 0.12, vis: "viseme_aa", dur: 0.08}, ...]

Design notes
------------
True phoneme-to-viseme mapping needs a forced aligner
(e.g. Montreal Forced Aligner or Gentle).  Those tools
require separate binaries and significant setup.

Instead we use a SIGNAL-BASED approach that:
1. Detects voiced / silence regions with librosa
2. Assigns viseme shapes probabilistically based on:
   - Spectral centroid  → selects front/back vowel group
   - Spectral contrast → fricatives vs. plosives vs. vowels
   - RMS energy        → jaw open amount

This is audio-reactive (like Beat Saber reaction) — it looks
natural at normal speech speeds without phoneme transcription.

If you want true phoneme accuracy, integrate:
  pip install phonemizer allosaurus
and replace `_energy_visemes()` with a phoneme-lookup table.
"""

import os
import json
import random
import numpy as np
import librosa

# ── All morph targets from the avatar spec ───────────────────
# Grouped by viseme "family" for energy-based assignment
_VISEME_FRONT_VOWELS  = ["viseme_E",  "viseme_I",  "viseme_aa"]
_VISEME_BACK_VOWELS   = ["viseme_O",  "viseme_U",  "viseme_aa"]
_VISEME_FRICATIVES    = ["viseme_FF", "viseme_SS", "viseme_TH"]
_VISEME_PLOSIVES      = ["viseme_PP", "viseme_DD", "viseme_kk", "viseme_CH"]
_VISEME_NASAL_APPROX  = ["viseme_nn", "viseme_RR"]
_SILENCE_VISEME       = "viseme_PP"   # mouth closed / rest pose

# ── Analysis parameters ───────────────────────────────────────
_FRAME_LENGTH = 2048   # FFT window (samples)
_HOP_LENGTH   = 512    # Hop between frames
_SR_TARGET    = 22050  # Resample to this rate for consistency


def extract_visemes(wav_path: str) -> list[dict]:
    """
    Analyse `wav_path` and return a list of viseme events.

    Parameters
    ----------
    wav_path : str
        Path to the synthesised reply WAV file.

    Returns
    -------
    visemes : list[dict]
        Each dict has:
          t   (float) — time in seconds
          vis (str)   — morph target name
          dur (float) — duration in seconds (how long to hold)
    """
    # ── Load audio ────────────────────────────────────────────
    y, sr = librosa.load(wav_path, sr=_SR_TARGET, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)
    print(f"[lipsync] Loaded {wav_path!r}  duration={duration:.2f}s  sr={sr}")

    # ── Compute per-frame features ────────────────────────────
    rms      = librosa.feature.rms(y=y, frame_length=_FRAME_LENGTH, hop_length=_HOP_LENGTH)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=_HOP_LENGTH)[0]
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=_HOP_LENGTH)
    # contrast shape: (n_bands, n_frames) — take mean across bands
    contrast_mean = contrast.mean(axis=0)

    # ── Normalise features to [0, 1] ─────────────────────────
    rms_norm      = _normalise(rms)
    centroid_norm = _normalise(centroid)
    contrast_norm = _normalise(contrast_mean)

    # ── Build viseme events from frames ───────────────────────
    n_frames  = len(rms_norm)
    frame_dur = _HOP_LENGTH / sr   # seconds per frame
    events    = []

    # ── Silence threshold ─────────────────────────────────────
    silence_rms = 0.05   # frames below this are mouth-closed

    for i in range(n_frames):
        t = i * frame_dur

        if rms_norm[i] < silence_rms:
            # Silence — mouth closed (jawOpen = 0 implied)
            vis = _SILENCE_VISEME
        else:
            vis = _pick_viseme(
                rms=rms_norm[i],
                centroid=centroid_norm[i],
                contrast=contrast_norm[i],
            )

        # ── Merge consecutive identical visemes ───────────────
        if events and events[-1]["vis"] == vis:
            events[-1]["dur"] = round(events[-1]["dur"] + frame_dur, 4)
        else:
            events.append({"t": round(t, 4), "vis": vis, "dur": round(frame_dur, 4)})

    # ── Add jawOpen events alongside vowel visemes ────────────
    events = _inject_jaw_open(events)

    print(f"[lipsync] Generated {len(events)} viseme events.")
    return events


# ─────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────

def _normalise(arr: np.ndarray) -> np.ndarray:
    """Min-max normalise to [0, 1]."""
    lo, hi = arr.min(), arr.max()
    if hi - lo < 1e-8:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def _pick_viseme(rms: float, centroid: float, contrast: float) -> str:
    """
    Heuristic viseme picker based on three spectral features.

    centroid  high → front vowels (E, I)
    centroid  low  → back vowels  (O, U)
    contrast  high → fricatives   (FF, SS, TH)
    contrast  low  → plosives     (PP, DD, kk, CH)
    mid-range      → nasals / approximants
    """
    if contrast > 0.65:
        # High spectral contrast = fricative / sibilant
        return random.choice(_VISEME_FRICATIVES)
    elif contrast < 0.25:
        # Low contrast + voiced = plosive
        return random.choice(_VISEME_PLOSIVES)
    elif centroid > 0.55:
        # Bright spectrum = front vowel
        return random.choice(_VISEME_FRONT_VOWELS)
    elif centroid < 0.35:
        # Dark spectrum = back vowel
        return random.choice(_VISEME_BACK_VOWELS)
    else:
        # Mid spectrum = nasal / approximant
        return random.choice(_VISEME_NASAL_APPROX)


def _inject_jaw_open(events: list[dict]) -> list[dict]:
    """
    Insert `jawOpen` events before vowel visemes so the jaw
    animation is separated from the lip shape animation.
    Three.js will blend both simultaneously.
    """
    vowel_visemes = set(
        _VISEME_FRONT_VOWELS + _VISEME_BACK_VOWELS + ["viseme_aa"]
    )
    extra = []
    for ev in events:
        if ev["vis"] in vowel_visemes and ev["dur"] > 0.05:
            extra.append({
                "t":   ev["t"],
                "vis": "jawOpen",
                "dur": ev["dur"] * 0.8,   # slightly shorter than vowel
            })
    combined = events + extra
    # Sort by time so the frontend can iterate in order
    combined.sort(key=lambda e: e["t"])
    return combined
