@echo off
REM ============================================================
REM  AI Avatar Chatbot — One-click installer
REM  Run from: ai_voice_chatbott\ai_avatar\
REM
REM  PREREQUISITES:
REM    - Python 3.10 installed (py -3.10)
REM    - Microsoft C++ Build Tools (for TTS==0.22.0):
REM      https://visualstudio.microsoft.com/visual-cpp-build-tools/
REM      Select: "Desktop development with C++"
REM ============================================================

echo [1/5] Creating tts_env with Python 3.10...
py -3.10 -m venv tts_env

echo [2/5] Activating tts_env...
call tts_env\Scripts\activate.bat

echo [3/5] Upgrading pip, setuptools, wheel...
python -m pip install --upgrade pip setuptools wheel

echo [4/5] Installing all core dependencies (pinned for Python 3.10)...
pip install ^
  flask==3.1.0 ^
  flask-cors==6.0.0 ^
  openai-whisper==20250625 ^
  ollama==0.3.3 ^
  numpy==1.26.4 ^
  scipy==1.13.1 ^
  librosa==0.10.2.post1 ^
  soundfile==0.12.1 ^
  torch==2.3.1 ^
  python-dotenv==1.0.1 ^
  requests==2.32.3

echo [5/5] Installing TTS==0.22.0 (requires C++ Build Tools)...
echo       If this fails, install Build Tools from:
echo       https://visualstudio.microsoft.com/visual-cpp-build-tools/
REM pip install TTS==0.22.0 --no-deps

echo.
echo ============================================================
echo  Done! To run the app:
echo    tts_env\Scripts\activate
echo    python main.py
echo ============================================================
pause
