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

# ── Model name — override via env if you want a different one ─
_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# ── Aishwarya's personality / language-matching system prompt ─────
_SYSTEM_PROMPT = (
    "You are Aishwarya, a friendly and helpful AI assistant with a warm personality. "
    "Rules you MUST follow:\n"
    "1. Always reply in the EXACT same language the user used. "
    "   If they write in Hindi, reply in Hindi. "
    "   If they write in Hinglish (Hindi + English mix), reply in Hinglish. "
    "   If they write in Punjabi, reply in Punjabi. "
    "   If they write in English, reply in English. Never switch languages unless the user does.\n"
    "2. Keep every reply to 3 sentences or fewer — short and natural.\n"
    "3. Be warm, concise, and conversational. Avoid lists or bullet points.\n"
    "4. Never mention that you are an AI language model or that you have limitations. "
    "   Just answer helpfully and move the conversation forward."
)


def generate_reply(user_message: str, language: str) -> str:
    """
    Generate a contextual reply from Aishwarya (LLaMA 3.2 via Ollama).

    Parameters
    ----------
    user_message : str
        Transcribed text from the user (any language).
    language     : str
        ISO-639-1 code detected by Whisper (e.g. "hi", "en").
        Used in a language-reinforcement hint injected into the
        user message so the model matches the language reliably.

    Returns
    -------
    reply : str
        Aishwarya's reply text (same language as user input).
    """
    # ── Language hint appended to the user message ────────────
    # This nudges the model even if the system prompt is
    # partially ignored in some ollama versions.
    lang_hint = _build_language_hint(language)
    augmented_message = f"{user_message}\n\n[{lang_hint}]"

    print(f"[llm] Sending to {_MODEL}: {user_message[:80]!r}  (lang={language})")

    try:
        response = ollama.chat(
            model=_MODEL,
            messages=[
                {"role": "system",    "content": _SYSTEM_PROMPT},
                {"role": "user",      "content": augmented_message},
            ],
            options={
                "temperature": 0.7,
                "top_p":       0.9,
                "num_predict": 100,  # Lower for faster response
                "num_thread":  8,    # Use more CPU cores for speed
            },
        )
        reply: str = response["message"]["content"].strip()
    except Exception as e:
        print(f"[llm] ERROR: {e}")
        # Fallback: Ollama not running or model not available
        reply = (
            "I'm sorry, I can't connect to my AI brain right now. "
            "Please make sure Ollama is running: open a terminal and type 'ollama serve', "
            f"then pull the model with 'ollama pull {_MODEL}'."
        )

    print(f"[llm] Aishwarya reply: {reply[:120]!r}")
    return reply


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
