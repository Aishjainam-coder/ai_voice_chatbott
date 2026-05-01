"""
stt.py — Speech-to-Text using OpenAI Whisper (local, offline)
==============================================================
Responsibilities:
  - Accept a raw audio file path (wav / webm / mp3 / etc.)
  - Transcribe it with Whisper
  - Auto-detect spoken language (returns ISO-639-1 code)
  - Return (transcript_text, language_code)

Whisper model used: "medium"
  • "base"   → fastest, lower accuracy
  • "medium" → good balance for Hindi / multilingual
  • "large"  → most accurate, slower
Set STT_MODEL env var to override (e.g. STT_MODEL=large).
"""

import os
from faster_whisper import WhisperModel

# ── Load model once at import time ──
_MODEL_NAME = os.getenv("STT_MODEL", "tiny")
# compute_type="int8" is much faster on CPU
_DEVICE = "cpu"
_COMPUTE_TYPE = "int8"

print(f"[stt] Loading Faster-Whisper model '{_MODEL_NAME}' on {_DEVICE} ({_COMPUTE_TYPE})...")
try:
    _model = WhisperModel(_MODEL_NAME, device=_DEVICE, compute_type=_COMPUTE_TYPE)
    print(f"[stt] Faster-Whisper ready.")
except Exception as e:
    print(f"[stt] ERROR: Could not load Faster-Whisper: {e}")
    _model = None


def transcribe(audio_path: str) -> tuple[str, str]:
    """
    Transcribe `audio_path` using Faster-Whisper.
    """
    if _model is None:
        print("[stt] Model not loaded, skipping transcription.")
        return "", "en"
    try:
        # beam_size=1 is faster; vad_filter removes silence before processing
        segments, info = _model.transcribe(
            audio_path, 
            beam_size=1, 
            vad_filter=True,
            language=None # Auto-detect
        )
        
        # segments is a generator, we need to join them
        text_parts = [s.text for s in segments]
        transcript = "".join(text_parts).strip()
        language = info.language

        print(f"[stt] Detected language: '{language}' (prob: {info.language_probability:.2f}) | Transcript: {transcript[:80]!r}")
        return transcript, language

    except Exception as e:
        print(f"[stt] Transcription error: {e}")
        return "", "en"
