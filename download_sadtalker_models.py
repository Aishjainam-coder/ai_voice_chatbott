"""
Manual SadTalker model downloader.
Run from inside your SadTalker folder:
    cd SadTalker
    python ../download_sadtalker_models.py
"""
import os, urllib.request, sys
from pathlib import Path

# Must be run from inside the SadTalker directory
if not Path("inference.py").exists():
    print("ERROR: Run this from inside the SadTalker folder!")
    print("  cd SadTalker")
    print("  python ../download_sadtalker_models.py")
    sys.exit(1)

MODELS = {
    "checkpoints/SadTalker_V0.0.2_256.safetensors":
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors",
    "checkpoints/SadTalker_V0.0.2_512.safetensors":
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors",
    "checkpoints/mapping_00109-model.pth.tar":
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar",
    "checkpoints/mapping_00229-model.pth.tar":
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar",
    "checkpoints/auido2exp_00300-model.pth":
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/auido2exp_00300-model.pth",
    "checkpoints/auido2pose_00140-model.pth":
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/auido2pose_00140-model.pth",
    "checkpoints/epoch_20.pth":
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/epoch_20.pth",
    "checkpoints/shape_predictor_68_face_landmarks.dat":
        "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/shape_predictor_68_face_landmarks.dat",
    "gfpgan/weights/GFPGANv1.4.pth":
        "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth",
    "gfpgan/weights/detection_Resnet50_Final.pth":
        "https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth",
    "gfpgan/weights/parsing_parsenet.pth":
        "https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth",
}

print("\n" + "="*55)
print("SadTalker Model Downloader")
print("="*55 + "\n")

for path, url in MODELS.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f"  ✅ Already exists: {path} ({size_mb:.0f} MB)")
        continue
    print(f"  ⬇  Downloading: {path}")
    try:
        def show_progress(block, block_size, total):
            if total > 0:
                done = block * block_size
                pct  = min(100, done * 100 // total)
                mb   = done / 1024 / 1024
                tot  = total / 1024 / 1024
                print(f"\r     {pct:3d}%  {mb:.1f}/{tot:.1f} MB", end="", flush=True)
        urllib.request.urlretrieve(url, path, show_progress)
        print(f"\r  ✅ Done: {path}  ({os.path.getsize(path)/1024/1024:.0f} MB)")
    except Exception as e:
        print(f"\r  ❌ Failed: {e}")

print("\n" + "="*55)
# Check what we have
ok  = [p for p in MODELS if os.path.exists(p)]
bad = [p for p in MODELS if not os.path.exists(p)]
print(f"Downloaded: {len(ok)}/{len(MODELS)} models")
if bad:
    print("Missing:")
    for p in bad: print(f"  ❌ {p}")
else:
    print("✅ All models ready! Run: python ../ai_chatbot.py")
print("="*55 + "\n")