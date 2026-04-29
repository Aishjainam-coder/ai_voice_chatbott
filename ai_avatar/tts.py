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

import subprocess

def synthesise(text: str, language: str, output_filename: str | None = None) -> str:
    """
    Convert `text` to speech and save to a WAV file.
    """
    voice = _VOICES.get(language, _VOICES["en"])
    
    if output_filename is None:
        output_filename = f"reply_{language}_{os.getpid()}.wav"
    
    final_wav = str(_OUTPUT_DIR / output_filename)
    temp_mp3 = final_wav.replace(".wav", ".mp3")

    print(f"[tts] Synthesising with Edge-TTS ({voice})")

    # edge-tts is asynchronous, so we run it in the event loop
    asyncio.run(_generate_audio(text, voice, temp_mp3))

    # Convert MP3 to WAV for lipsync analysis (scipy requirement)
    print(f"[tts] Converting to WAV: {final_wav}")
    try:
        # -y to overwrite, -i for input, then output
        subprocess.run([
            "ffmpeg", "-y", "-i", temp_mp3, 
            "-acodec", "pcm_s16le", "-ac", "1", "-ar", "16000", 
            final_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Cleanup temp MP3
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)
            
    except Exception as e:
        print(f"[tts] FFmpeg Conversion Error: {e}")
        # If conversion fails, we'll just try to return the MP3 data renamed as wav 
        # (though this will likely break lipsync, it prevents total crash)
        if os.path.exists(temp_mp3):
            os.rename(temp_mp3, final_wav)

    print(f"[tts] Written: {final_wav}")
    return final_wav

async def _generate_audio(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
