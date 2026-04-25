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
import whisper

# ── Load model once at import time so every request is fast ──
_MODEL_NAME = os.getenv("STT_MODEL", "medium")
print(f"[stt] Loading Whisper model '{_MODEL_NAME}' … (first run downloads ~1.5 GB)")
_model = whisper.load_model(_MODEL_NAME)
print(f"[stt] Whisper '{_MODEL_NAME}' ready.")


def transcribe(audio_path: str) -> tuple[str, str]:
    """
    Transcribe `audio_path` and detect the spoken language.

    Parameters
    ----------
    audio_path : str
        Absolute or relative path to any audio file Whisper
        can read (wav, mp3, webm, ogg, flac, …).

    Returns
    -------
    transcript : str
        Full transcription text.
    language   : str
        ISO-639-1 language code detected by Whisper
        (e.g. "en", "hi", "pa", "ta", "ur").
    """
    # fp16=False forces CPU-safe float32; set True only on CUDA
    use_fp16 = False

    # Whisper's transcribe() handles resampling internally via
    # ffmpeg, so any sample-rate / channel count works.
    result = _model.transcribe(
        audio_path,
        fp16=use_fp16,
        # task="transcribe" keeps original language
        # task="translate" would force English output
        task="transcribe",
    )

    transcript: str = result["text"].strip()
    language: str   = result.get("language", "en")  # ISO code

    print(f"[stt] Detected language: '{language}'  |  Transcript: {transcript[:80]!r}")
    return transcript, language
