"""
Creates assets/character_idle.mp4 from your avatar image.
Run once before starting the chatbot: python create_idle_video.py
"""
import os
from pathlib import Path

out_path = Path("assets/character_idle.mp4")
DURATION, FPS = 3, 24
os.makedirs("assets", exist_ok=True)

# Find image
img_path = None
for p in ["assets/character.png","assets/character.jpg"]:
    if Path(p).exists(): img_path = p; break
if not img_path:
    print("ERROR: No avatar image found. Copy your image to assets/character.png")
    raise SystemExit(1)
print(f"Using: {img_path}")

# Try moviepy
try:
    from moviepy.editor import ImageClip
    ImageClip(img_path, duration=DURATION).write_videofile(
        str(out_path), fps=FPS, codec="libx264", audio=False, logger=None)
    print(f"✅ {out_path} (moviepy)"); raise SystemExit(0)
except SystemExit: raise
except Exception as e: print(f"moviepy: {e}")

# Try imageio
try:
    import imageio, numpy as np
    from PIL import Image
    arr = np.array(Image.open(img_path).convert("RGB"))
    w = imageio.get_writer(str(out_path), fps=FPS, codec="libx264",
                           ffmpeg_params=["-pix_fmt","yuv420p"])
    for _ in range(DURATION*FPS): w.append_data(arr)
    w.close()
    print(f"✅ {out_path} (imageio)"); raise SystemExit(0)
except SystemExit: raise
except Exception as e: print(f"imageio: {e}")

# Try OpenCV
try:
    import cv2, numpy as np
    from PIL import Image
    arr = np.array(Image.open(img_path).convert("RGB"))
    frame = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    h, w = frame.shape[:2]
    out = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w,h))
    for _ in range(DURATION*FPS): out.write(frame)
    out.release()
    print(f"✅ {out_path} (OpenCV)"); raise SystemExit(0)
except SystemExit: raise
except Exception as e: print(f"OpenCV: {e}")

print("❌ Install moviepy, imageio[ffmpeg], or opencv-python")
raise SystemExit(2)