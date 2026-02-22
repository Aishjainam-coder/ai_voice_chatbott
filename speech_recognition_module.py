"""
Speech Recognition - converts mic audio to text via Google STT (free tier, local processing)
No API key required for basic usage.
"""
import speech_recognition as sr

class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def transcribe_from_file(self, audio) -> str:
        return self.transcribe(audio)

    def transcribe(self, audio) -> str:
        if audio is None: return ""
        path = audio[0] if isinstance(audio, tuple) else audio
        if not path or not str(path).strip(): return ""
        try:
            with sr.AudioFile(str(path)) as src:
                self.recognizer.adjust_for_ambient_noise(src, duration=0.2)
                data = self.recognizer.record(src)
            return self.recognizer.recognize_google(data).strip()
        except sr.UnknownValueError: return ""
        except sr.RequestError as e: return f"Error: Speech service unavailable - {e}"
        except Exception as e:       return f"Error: {e}"