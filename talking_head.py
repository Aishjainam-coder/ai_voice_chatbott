"""
Talking Head Module
Attempts Wav2Lip animation. Falls back to audio-only if not installed.
Install Wav2Lip for full lip-sync: https://github.com/Rudrabha/Wav2Lip
"""
import os, subprocess
from pathlib import Path

class TalkingHead:
    def __init__(self, wav2lip_path=None):
        self.wav2lip_path = wav2lip_path or self._find()
        self.tmp = Path("temp_audio_video"); self.tmp.mkdir(exist_ok=True)

    def _find(self):
        for p in [Path.cwd()/"Wav2Lip", Path.cwd()/"wav2lip",
                  Path.home()/"Wav2Lip", Path.home()/"wav2lip"]:
            if p.exists() and (p/"inference.py").exists(): return str(p)
        return None

    def is_available(self):
        return self.wav2lip_path and os.path.exists(
            os.path.join(self.wav2lip_path,"inference.py"))

    def generate_video(self, face_path, audio_path, out_path=None):
        """Returns (video_path, audio_path). video_path=None if Wav2Lip unavailable."""
        if not audio_path or not os.path.exists(str(audio_path)):
            return None, audio_path
        if not self.is_available():
            print("⚠ Wav2Lip not found — CSS animation used instead.")
            return None, audio_path
        if out_path is None:
            out_path = self.tmp / f"out_{os.urandom(4).hex()}.mp4"
        ckpt = os.path.join(self.wav2lip_path,"checkpoints","wav2lip.pth")
        if not os.path.exists(ckpt): return None, audio_path
        cmd = ["python", os.path.join(self.wav2lip_path,"inference.py"),
               "--checkpoint_path", ckpt, "--face", face_path,
               "--audio", audio_path, "--outfile", str(out_path),
               "--pads","0","20","0","0","--nosmooth"]
        try:
            r = subprocess.run(cmd, cwd=self.wav2lip_path,
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0: return None, audio_path
            return str(out_path), audio_path
        except Exception as e:
            print(f"Wav2Lip error: {e}"); return None, audio_path

talking_head = TalkingHead()