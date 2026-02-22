# 🤖 JASON - Your AI Assistant

**Voice Input • Voice Output • Animated Avatar • Lip-Sync • Emotions**

A complete AI avatar chatbot that:
- 🎤 **Voice Input** - Speak naturally to Jason!
- 🔊 **Voice Output** - Jason responds with natural speech and lip-sync
- 🎭 **Animated Avatar** - Your character comes to life with emotions
- 👄 **Lip-Sync Animation** - Perfect mouth movements with speech
- 💬 **Real-time Conversation** - Seamless voice-to-voice interaction
- 🆓 **100% Free** - All models run locally, no API costs

---

## Quick Start

### 1. Install Python Dependencies

```bash
cd "c:\Users\hp\ai chatbot"
pip install -r requirements.txt
```

**Note:** Voice input uses Gradio's built-in mic (records in browser) - **no PyAudio needed!** Works with Python 3.14.

### 2. Install Ollama (Free Local AI)

1. Download from **https://ollama.com**
2. Install and run Ollama
3. Pull a model (in terminal):
   ```bash
   ollama pull llama3.2
   ```
   Or: `ollama pull mistral` (smaller, faster)

### 3. Add Your CEO/Character Image

- Create folder: `assets/`
- Add image: `assets/character.png` (or .jpg)
- Use a clear face photo for best results

### 4. Run the Chatbot

```bash
python ai_chatbot.py
```

Then open: **http://127.0.0.1:7860**

---

## 🎯 How to Use

### Voice Mode (Recommended):
1. **Look at your AI Avatar** at the top of the screen
2. **Click the microphone** 🎤 to record your voice
3. **Speak naturally** - ask anything to your AI avatar
4. **Click "Speak & Respond"** or wait for auto-processing
5. **Watch the magic** - AI avatar responds with voice + perfect lip-sync animation!

### Text Mode (Backup):
- Type your message in the text box if voice doesn't work
- Click "Send Text" or press Enter

### Interface Layout:
- **🤖 AI Avatar** (left) - Large animated character display
- **🎤 Voice Controls** (right) - Microphone, record button, status
- **💬 Conversation** (bottom) - Chat history
- **📝 Text Input** (collapsed) - Backup text option

---

### 5. Optional: Professional Talking Head Animation (Wav2Lip)

For realistic video lip-sync animation:

1. **Install Git** (if not already installed): Download from https://git-scm.com/downloads
2. **Run setup script**: `setup_wav2lip.bat`
3. **Download model**: Get `wav2lip.pth` from https://github.com/Rudrabha/Wav2Lip/releases/tag/models
4. **Place model**: Put `wav2lip.pth` in `Wav2Lip/checkpoints/wav2lip.pth`

**Note:** Wav2Lip creates professional video animation but takes 30-60 seconds per response. If not set up, the app falls back to image-based animation.

---

## Features

| Feature | Technology |
|---------|------------|
| **Voice Input** | Gradio mic (browser) + SpeechRecognition |
| AI Chat | Ollama + Llama/Mistral (local) |
| Sentiment Analysis | DistilBERT (transformers) |
| Emotions | 12 emotions: happy, sad, empathetic, calm, etc. |
| Character Display | Your image + emotion overlay |
| **Talking Head Video** | Wav2Lip lip-sync animation |
| Text-to-Speech | Edge TTS (high quality, offline) |
| UI | Gradio |

## How to Use Voice Input & Talking Head

1. **Type your message** - Send text to the AI
2. **AI responds** - Generates reply with emotion analysis
3. **Watch the video** - Character's face animates with realistic lip sync!
4. **Automatic processing** - Audio generated, then synced with your face image

The talking head uses Wav2Lip to create professional video animation from your static image + AI-generated speech.

---

## Using CEO Photo

**Yes, you can use your company CEO's photo!** 

1. Place the image in `assets/character.png`
2. The chatbot will display it with emotion badges
3. For professional use: ensure you have permission to use the image

---

## Requirements

- **Python** 3.8+
- **RAM**: 8GB+ (16GB recommended for LLM)
- **Disk**: ~4GB for Ollama models
- **GPU**: Optional (faster with NVIDIA GPU)

---

## Troubleshooting

**"Ollama not connecting"**
- Ensure Ollama is running (check system tray)
- Run `ollama list` to verify models

**Voice input not working**
- Uses Gradio's browser mic - allow microphone permission when prompted
- Click the mic icon, speak, then click "Submit Voice"
- Speech recognition uses Google's free API (internet needed for voice)

**"Could not understand audio"**
- Speak clearly and wait for the 🎤 button to finish listening
- Check microphone volume in Windows Settings
- Try speaking closer to microphone

**Slow first run**
- First time loads sentiment model (~250MB) - one-time download
- Ollama downloads model on first use

**No character image**
- Add `assets/character.png` - placeholder shows until you do

**Lip sync not animating**
- Make sure to click "🔊 Speak with Lip Sync" button (not just "Speak")
- Character mouth animates during speech playback

---

## File Structure

```
ai chatbot/
├── ai_chatbot.py       # Main app
├── sentiment_analyzer.py
├── character_display.py
├── requirements.txt
├── assets/
│   └── character.png   # Your CEO/character image
└── README.md
```
