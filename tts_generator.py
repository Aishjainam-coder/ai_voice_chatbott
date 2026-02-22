"""
TTS Generator - Uses edge-tts (free, local, natural voices)
Different voices and rates per emotion for expressive speech.
"""
import asyncio, os
from pathlib import Path

class TTSGenerator:
    VOICES = {
        "happy":        "en-US-JennyNeural",
        "excited":      "en-US-JennyNeural",
        "sad":          "en-US-AriaNeural",
        "empathetic":   "en-US-AriaNeural",
        "calm":         "en-US-AriaNeural",
        "confident":    "en-US-GuyNeural",
        "concerned":    "en-US-AriaNeural",
        "thoughtful":   "en-US-AriaNeural",
        "professional": "en-US-GuyNeural",
    }
    RATES = {
        "excited":"+15%","happy":"+8%","calm":"+0%",
        "sad":"-10%","empathetic":"-5%","thoughtful":"-5%",
        "confident":"+5%","concerned":"-3%","professional":"+0%",
    }

    def __init__(self):
        self.tmp = Path("temp_audio")
        self.tmp.mkdir(exist_ok=True)

    async def _gen(self, text, voice, rate, path):
        import edge_tts
        await edge_tts.Communicate(text, voice, rate=rate).save(path)

    def generate_audio(self, text: str, emotion: str = "calm") -> str | None:
        if not text or not text.strip(): return None
        voice = self.VOICES.get(emotion, "en-US-AriaNeural")
        rate  = self.RATES.get(emotion, "+0%")
        path  = str(self.tmp / f"tts_{os.urandom(4).hex()}.mp3")
        try:
            try:
                asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    pool.submit(asyncio.run, self._gen(text,voice,rate,path)).result()
            except RuntimeError:
                asyncio.run(self._gen(text, voice, rate, path))
            return path if os.path.exists(path) else None
        except Exception as e:
            print(f"TTS error: {e}"); return None

    def generate(self, text: str, emotion: str = "calm") -> str | None:
        return self.generate_audio(text, emotion)

    def cleanup(self, keep=5):
        files = sorted(self.tmp.glob("*.mp3"),
                       key=lambda f: f.stat().st_mtime, reverse=True)
        for f in files[keep:]: f.unlink(missing_ok=True)

tts_generator = TTSGenerator()