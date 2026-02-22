@echo off
echo ================================================
echo  SadTalker Setup for JASON AI Avatar
echo ================================================
echo.

cd /d "%~dp0"

REM ── 1. Fix numpy for Python 3.12+ ─────────────────────────────────────────
echo [1/5] Installing compatible numpy...
pip install "numpy<2.0"
if errorlevel 1 (
    echo Trying numpy 1.26.4 specifically...
    pip install numpy==1.26.4
)

REM ── 2. Clone SadTalker if not already done ────────────────────────────────
echo.
echo [2/5] Cloning SadTalker...
if exist "SadTalker\inference.py" (
    echo SadTalker already cloned, skipping.
) else (
    git clone https://github.com/OpenTalker/SadTalker
    if errorlevel 1 (
        echo ERROR: git clone failed. Install git from https://git-scm.com
        pause && exit /b
    )
)

REM ── 3. Install SadTalker deps ─────────────────────────────────────────────
echo.
echo [3/5] Installing SadTalker dependencies...
cd SadTalker
pip install "numpy<2.0"
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

REM ── 4. Download models ────────────────────────────────────────────────────
echo.
echo [4/5] Downloading model checkpoints (~700MB, one time only)...

REM SadTalker moved to gdown-based download
pip install gdown

REM Try the official download script (path changed in newer versions)
if exist "scripts\download_models.py" (
    python scripts\download_models.py
) else if exist "script\download_models.py" (
    python script\download_models.py
) else (
    echo Download script not found - downloading manually...
    python -c "
import os, urllib.request
os.makedirs('checkpoints', exist_ok=True)
os.makedirs('gfpgan/weights', exist_ok=True)

files = {
    'checkpoints/SadTalker_V0.0.2_256.safetensors':
        'https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors',
    'checkpoints/SadTalker_V0.0.2_512.safetensors':
        'https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors',
    'checkpoints/mapping_00109-model.pth.tar':
        'https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar',
    'checkpoints/mapping_00229-model.pth.tar':
        'https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar',
    'gfpgan/weights/GFPGANv1.4.pth':
        'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth',
}
for path, url in files.items():
    if os.path.exists(path):
        print(f'Already exists: {path}')
        continue
    print(f'Downloading {path}...')
    try:
        urllib.request.urlretrieve(url, path)
        print(f'  OK')
    except Exception as e:
        print(f'  FAILED: {e}')
print('Done!')
"
)

REM ── 5. Verify ─────────────────────────────────────────────────────────────
echo.
echo [5/5] Verifying...
if exist "checkpoints\SadTalker_V0.0.2_256.safetensors" (
    echo ✅ Checkpoints found!
) else (
    echo ⚠  Checkpoints not found - check download step above
)

cd ..
echo.
echo ================================================
echo  Setup complete! Now run:  python ai_chatbot.py
echo ================================================
pause