"""
tts.py — Text-to-Speech using Microsoft Edge-TTS
================================================
Responsibilities:
  - Accept reply text + language code
  - Use Microsoft Edge's high-quality online voices
  - Synthesise speech and write a .wav file
  - Return the path to the generated .wav

NOTE: This replaces Coqui XTTS-v2 to avoid the need for C++ Build Tools.
It is extremely fast, high-quality, and supports many languages including Hindi.
"""

import os
import asyncio
import pathlib
import edge_tts

# ── Output directory for generated audio ─────────────────────
_OUTPUT_DIR = pathlib.Path(os.getenv("TTS_OUTPUT_DIR", "temp_audio"))
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Voice mapping for different languages ─────────────────────
# You can find more voices with: edge-tts --list-voices
_VOICES = {
    "hi": "hi-IN-SwaraNeural",    # Hindi Female
    "en": "en-US-AvaNeural",      # English Female (Professional)
    "pa": "hi-IN-SwaraNeural",    # Fallback Punjabi to Hindi
    "ur": "ur-PK-UzmaNeural",     # Urdu
}

def synthesise(text: str, language: str, output_filename: str | None = None) -> str:
    """
    Convert `text` to speech and save to a WAV file.
    """
    voice = _VOICES.get(language, _VOICES["en"])
    
    if output_filename is None:
        output_filename = f"reply_{language}_{os.getpid()}.wav"
    wav_path = str(_OUTPUT_DIR / output_filename)

    print(f"[tts] Synthesising with Edge-TTS ({voice}) -> {wav_path}")

    # edge-tts is asynchronous, so we run it in the event loop
    asyncio.run(_generate_audio(text, voice, wav_path))

    print(f"[tts] Written: {wav_path}")
    return wav_path

async def _generate_audio(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
