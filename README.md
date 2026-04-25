# 🤖 JASON - Your AI Assistant with Beyond Presence Avatar

**Voice Input • Voice Output • Cloud Avatar • Lip-Sync • Emotions**

A complete AI avatar chatbot that:
- 🎤 **Voice Input** - Speak naturally to Jason!
- 🔊 **Voice Output** - Jason responds with natural speech
- 🌐 **Cloud 3D Avatar** - Professional Beyond Presence avatar with full animation
- 👄 **Automatic Lip-Sync** - Perfect mouth movements with speech (Beyond Presence handles it)
- 💬 **Real-time Conversation** - Seamless voice-to-voice interaction
- 😊 **Emotion Expressions** - Avatar reacts to conversation tone
- 🆓 **100% Free for Core** - Ollama LLM runs locally, Beyond Presence API for avatar

---

## Quick Start

### 1. Install Python Dependencies

```bash
cd c:\Users\acre\ai_voice_chatbott
pip install -r requirements.txt
```

**Note:** Voice input uses Gradio's built-in mic (records in browser) - **no PyAudio needed!**

### 2. Install Ollama (Free Local AI)

1. Download from **https://ollama.com**
2. Install and run Ollama
3. Pull a model (in terminal):
   ```bash
   ollama pull llama3.2
   ```
   Or: `ollama pull mistral` (smaller, faster)

### 3. Configure Beyond Presence Avatar (REQUIRED)

You need a Beyond Presence account for the cloud avatar:

1. **Create Beyond Presence Account**:
   - Go to https://beyondpresence.com
   - Sign up for free account

2. **Upload Your Avatar**:
   - In the Beyond Presence dashboard, upload your `.glb` file
   - Or use a provided template avatar
   - Copy the **Avatar ID**

3. **Get API Key**:
   - Go to Account > API Keys
   - Copy your API key

4. **Edit `.env` file** in this folder:
   ```bash
   BEYOND_PRESENCE_API_KEY=sk-your_actual_key_here
   AVATAR_ID=your_avatar_id_here
   BEYOND_PRESENCE_API_ENDPOINT=https://api.beyondpresence.com/v1
   OLLAMA_MODEL=llama3.2
   ```

### 4. Run JASON

```bash
python ai_chatbot.py
```

Then open: **http://127.0.0.1:7860**

You should see:
- ✅ **Beyond Presence Avatar ACTIVE** status message
- 🌐 Your cloud avatar ready to interact
- 🎤 Voice input ready
- 💬 Conversation history below

---

## 🎯 How to Use

### Voice Mode (Recommended):
1. **Look at your Beyond Presence Avatar** at the top
2. **Click the microphone** 🎤 button
3. **Speak naturally** - ask anything
4. **AI responds with**:
   - Voice output (text-to-speech)
   - Avatar animates with emotions
   - Perfect lip-sync (Beyond Presence handles it)
   - Conversation displayed below

### Text Mode (Backup):
- Type your message if voice doesn't work
- Click "Send ➤" or press Enter

### Features:
- **Emotion Detection**: Avatar shows different emotions based on conversation
- **Manual Emotion Override**: Choose avatar emotion from dropdown in "Manual Emotion Override"
- **Auto Lip-Sync**: Beyond Presence automatically animates the mouth
- **Face-Only Display**: Just the face shows, not full body
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
