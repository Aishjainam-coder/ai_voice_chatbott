"""
llm.py — AI Brain using Ollama + LLaMA 3
=========================================
Responsibilities:
  - Accept user message text + detected language code
  - Build a system prompt that instructs Aishwarya to reply
    in the SAME language the user spoke in
  - Stream the reply from the locally running Ollama server
  - Return the full reply string

Prerequisites:
  1. Ollama installed and running (ollama serve)
  2. Model pulled: ollama pull llama3
"""

import os
import ollama
import json

# ── Model name — override via env if you want a different one ─
_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# ── Aishwarya's personality / language-matching system prompt ─────
_SYSTEM_PROMPT = (
    "You are Aishwarya, a friendly and helpful AI assistant with a warm personality. "
    "Rules you MUST follow:\n"
    "1. Always reply in the EXACT same language the user used.\n"
    "2. Keep every reply to 2 sentences or fewer — extremely short.\n"
    "3. Be warm, concise, and conversational. Avoid lists or bullet points.\n"
    "4. You MUST output your response in JSON format ONLY with the following keys:\n"
    '   "text": Your conversational reply string.\n'
    '   "emotion": One of [ "happy", "sad", "angry", "surprised", "neutral" ].\n'
    "Example: { \"text\": \"नमस्ते! मैं आपकी कैसे मदद कर सकती हूँ?\", \"emotion\": \"happy\" }\n"
    "Do NOT include any other text before or after the JSON."
)


def generate_reply(user_message: str, language: str) -> tuple[str, str]:
    """
    Generate a contextual reply from Aishwarya (LLaMA 3.2 via Ollama).

    Returns
    -------
    (reply_text, emotion) : tuple[str, str]
    """
    lang_hint = _build_language_hint(language)
    augmented_message = f"{user_message}\n\n[{lang_hint}]"

    print(f"[llm] Sending to {_MODEL}: {user_message[:80]!r}")

    try:
        response = ollama.chat(
            model=_MODEL,
            messages=[
                {"role": "system",    "content": _SYSTEM_PROMPT},
                {"role": "user",      "content": augmented_message},
            ],
            options={
                "temperature": 0.6,
                "num_predict": 80,
                "num_thread":  8,
                "top_k": 20,
                "top_p": 0.9,
            },
        )
        raw_content = response["message"]["content"].strip()
        
        # ── Parse JSON output ─────────────────────────────────
        try:
            # Try to find JSON block if the model added chatter or formatting
            clean_content = raw_content.replace('```json', '').replace('```', '').strip()
            if "{" in clean_content and "}" in clean_content:
                start = clean_content.find("{")
                end = clean_content.rfind("}") + 1
                json_str = clean_content[start:end]
                data = json.loads(json_str)
            else:
                data = json.loads(clean_content)
            
            reply   = data.get("text", raw_content)
            emotion = data.get("emotion", "neutral")
        except Exception as json_err:
            print(f"[llm] JSON Parse Warning: {json_err}. Content: {raw_content[:100]!r}")
            # Fallback: if it's not valid JSON, we'll try to use the raw content as text
            reply   = raw_content
            emotion = "neutral"

    except Exception as e:
        print(f"[llm] ERROR: {e}")
        reply = "I'm sorry, I can't connect to my AI brain right now."
        emotion = "sad"

    print(f"[llm] Aishwarya ({emotion}): {reply[:120]!r}")
    return reply, emotion


# ─────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────

def _build_language_hint(language: str) -> str:
    """
    Return a human-readable instruction injected as a language
    reminder into the user turn so the LLM stays on-language.
    """
    _lang_names = {
        "hi": "Please reply in Hindi (हिंदी में जवाब दें).",
        "en": "Please reply in English.",
        "pa": "Please reply in Punjabi (ਪੰਜਾਬੀ ਵਿੱਚ ਜਵਾਬ ਦਿਓ).",
        "ta": "Please reply in Tamil (தமிழில் பதிலளிக்கவும்).",
        "te": "Please reply in Telugu (తెలుగులో సమాధానం ఇవ్వండి).",
        "mr": "Please reply in Marathi (मराठीत उत्तर द्या).",
        "bn": "Please reply in Bengali (বাংলায় উত্তর দিন).",
        "ur": "Please reply in Urdu (اردو میں جواب دیں).",
        "gu": "Please reply in Gujarati (ગુજરાતીમાં જવાબ આપો).",
        "kn": "Please reply in Kannada (ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸಿ).",
    }
    return _lang_names.get(language, f"Please reply in the same language as the user (detected: {language}).")
