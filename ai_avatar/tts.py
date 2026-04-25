"""
tts.py — Text-to-Speech using Coqui XTTS-v2
=============================================
Responsibilities:
  - Accept reply text + language code
  - Choose the correct voice / speaker for that language
  - Synthesise speech and write a .wav file
  - Return the path to the generated .wav

XTTS-v2 supports multilingual synthesis from the same model.
The speaker reference wav files embedded below are short
reference clips used by XTTS for voice cloning/matching.

If you have a custom voice reference file, point the
SPEAKER_WAV env var at it:  SPEAKER_WAV=/path/to/ref.wav

First run will download the XTTS-v2 model (~2 GB).
"""

import os
import tempfile
import pathlib
import numpy as np
import soundfile as sf
from TTS.api import TTS

# ── Output directory for generated audio ─────────────────────
_OUTPUT_DIR = pathlib.Path(os.getenv("TTS_OUTPUT_DIR", "temp_audio"))
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── XTTS-v2 language codes that the model natively supports ──
# For languages NOT in this set we fall back to English.
_XTTS_SUPPORTED = {
    "en", "hi", "es", "fr", "de", "it", "pt", "pl",
    "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hu",
}

# ── Hinglish / regional Indian language → use Hindi voice ────
_HINDI_FAMILY = {"hi", "ur", "pa", "mr", "gu", "bho"}

# ── Speaker reference wavs ────────────────────────────────────
# These short WAV clips tell XTTS the desired voice timbre.
# You can replace them with your own recording:
#   - 6–30 seconds of clear speech, WAV 22 050 Hz mono
# Env override:  SPEAKER_WAV_EN / SPEAKER_WAV_HI
_SPEAKER_WAV_EN = os.getenv("SPEAKER_WAV_EN", "")
_SPEAKER_WAV_HI = os.getenv("SPEAKER_WAV_HI", "")

# ── Load the XTTS-v2 model once at import time ────────────────
print("[tts] Loading Coqui XTTS-v2 model … (first run downloads ~2 GB)")
_tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
print("[tts] XTTS-v2 ready.")


def synthesise(text: str, language: str, output_filename: str | None = None) -> str:
    """
    Convert `text` to speech and save to a WAV file.

    Parameters
    ----------
    text            : str   — The reply text to synthesise.
    language        : str   — ISO-639-1 code (e.g. "hi", "en").
    output_filename : str   — Optional filename inside temp_audio/.

    Returns
    -------
    wav_path : str — Absolute path to the written .wav file.
    """
    xtts_lang  = _resolve_xtts_language(language)
    speaker_wav = _resolve_speaker_wav(xtts_lang)

    # ── Choose output path ────────────────────────────────────
    if output_filename is None:
        output_filename = f"reply_{language}_{os.getpid()}.wav"
    wav_path = str(_OUTPUT_DIR / output_filename)

    print(f"[tts] Synthesising ({xtts_lang}) → {wav_path}")

    if speaker_wav and pathlib.Path(speaker_wav).exists():
        # Voice-cloning mode — uses the provided reference clip
        _tts.tts_to_file(
            text=text,
            language=xtts_lang,
            speaker_wav=speaker_wav,
            file_path=wav_path,
        )
    else:
        # Default built-in speaker for the language
        # XTTS-v2 has a set of named speakers; "Ana Florence" is
        # a good neutral female English voice.
        _tts.tts_to_file(
            text=text,
            language=xtts_lang,
            speaker="Ana Florence",
            file_path=wav_path,
        )

    print(f"[tts] Written: {wav_path}")
    return wav_path


# ─────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────

def _resolve_xtts_language(language: str) -> str:
    """
    Map detected Whisper language codes to XTTS-v2 language tags.
    Hindi family and Hinglish → "hi".
    Unsupported → fall back to "en".
    """
    if language in _HINDI_FAMILY:
        return "hi"
    if language in _XTTS_SUPPORTED:
        return language
    # Handle zh, zh-TW → zh-cn
    if language.startswith("zh"):
        return "zh-cn"
    # Default fallback
    return "en"


def _resolve_speaker_wav(xtts_lang: str) -> str:
    """Return the appropriate speaker reference WAV path."""
    if xtts_lang == "hi" and _SPEAKER_WAV_HI:
        return _SPEAKER_WAV_HI
    if _SPEAKER_WAV_EN:
        return _SPEAKER_WAV_EN
    return ""
