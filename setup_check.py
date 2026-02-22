#!/usr/bin/env python3
"""
JASON Setup Validator
Checks dependencies and guides setup
"""

import os
import sys

print("\n" + "="*60)
print("🎤 JASON - AI Voice Assistant | Setup Checker")
print("="*60 + "\n")

# Check Python version
print(f"✅ Python: {sys.version.split()[0]}")

# Check dependencies
dependencies = {
    "gradio": "Web UI",
    "PIL": "Image processing",
    "edge_tts": "High-quality text-to-speech",
    "speech_recognition": "Voice recognition",
    "torch": "AI models",
    "transformers": "Sentiment analysis",
    "cv2": "Video processing",
    "librosa": "Audio processing",
}

missing = []
for dep, desc in dependencies.items():
    try:
        __import__(dep)
        print(f"✅ {dep:15} - {desc}")
    except ImportError:
        print(f"❌ {dep:15} - MISSING ({desc})")
        missing.append(dep)

# Check image
if os.path.exists("assets/character.png"):
    size = os.path.getsize("assets/character.png") / 1024
    print(f"\n✅ Image found: assets/character.png ({size:.1f} KB)")
else:
    print(f"\n⚠️  Image NOT found at: assets/character.png")
    print("   👉 Please save your face image there!")

# Ollama check
try:
    from ollama import list as ollama_list
    print("✅ Ollama is available")
except:
    print("⚠️  Ollama not installed (will use fallback responses)")

print("\n" + "="*60)
if missing:
    print(f"📦 Install missing: pip install {' '.join(missing)}")
else:
    print("✅ All dependencies installed!")

print("\n🚀 To start JASON:")
print("   python jason_chatbot.py")
print("\n" + "="*60 + "\n")
