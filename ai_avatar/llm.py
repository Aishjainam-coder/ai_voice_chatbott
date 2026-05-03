"""
llm.py — AI Brain using Ollama + LLaMA 3
=========================================
"""

import os
import re
import ast
import ollama
import json

_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

_SYSTEM_PROMPT = (
    "You are Aishwarya, a friendly AI assistant with a warm personality.\n"
    "You MUST respond with a SINGLE valid JSON object and absolutely nothing else.\n"
    "The JSON must have exactly two keys: 'text' and 'emotion'.\n"
    "\n"
    "RULES:\n"
    "1. Always reply in the EXACT same language the user used.\n"
    "2. Keep the 'text' value to 2 sentences or fewer — extremely short.\n"
    "3. Be warm, concise, and conversational. No lists or bullet points.\n"
    "4. 'emotion' must be exactly one of: happy, sad, angry, surprised, neutral.\n"
    "5. Use ONLY double quotes. Never single quotes.\n"
    "6. ONE JSON object only — not two, not split across lines.\n"
    "7. No text before or after the JSON. No markdown. No code fences.\n"
    "\n"
    "CORRECT OUTPUT EXAMPLE:\n"
    "{\"text\": \"Hello! How can I help you today?\", \"emotion\": \"happy\"}\n"
    "\n"
    "WRONG OUTPUT EXAMPLES (never do these):\n"
    "{\"text\": \"Hello!\"}. {\"emotion\": \"happy\"}\n"
    "Here is my response: {\"text\": \"Hello!\", \"emotion\": \"happy\"}\n"
    "```json\n{\"text\": \"Hello!\", \"emotion\": \"happy\"}\n```\n"
)


def _parse_llm_output(raw: str) -> tuple[str, str]:
    """
    Robustly extract (text, emotion) from whatever the LLM returned.
    Handles: proper JSON, split JSON objects, single-quote JSON,
    escaped JSON, partial JSON, and plain text fallback.
    """
    # Step 1: strip markdown code fences
    clean = raw.replace("```json", "").replace("```", "").strip()

    # Step 2: FIX — detect and merge split JSON objects
    # e.g. {"text": "..."}.  {"emotion": "neutral"}
    all_blocks = re.findall(r"\{[^{}]+\}", clean, re.DOTALL)
    if len(all_blocks) > 1:
        merged = {}
        for block in all_blocks:
            try:
                merged.update(json.loads(block))
                continue
            except Exception:
                pass
            try:
                merged.update(ast.literal_eval(block))
                continue
            except Exception:
                pass
            # try fixing single quotes
            try:
                merged.update(json.loads(block.replace("'", '"')))
            except Exception:
                pass
        if "text" in merged:
            text = str(merged.get("text", "")).strip()
            emotion = str(merged.get("emotion", "neutral")).strip().lower()
            if text:
                return text, _safe_emotion(emotion)

    # Step 3: extract the outermost {...} block
    brace_match = re.search(r"\{.*\}", clean, re.DOTALL)
    json_str = brace_match.group(0) if brace_match else clean

    # Step 4: standard JSON parse
    try:
        data = json.loads(json_str)
        text    = data.get("text", "").strip()
        emotion = data.get("emotion", "neutral").strip().lower()
        if text:
            return text, _safe_emotion(emotion)
    except Exception:
        pass

    # Step 5: ast.literal_eval for single-quote dicts
    try:
        data = ast.literal_eval(json_str)
        text    = data.get("text", "").strip()
        emotion = data.get("emotion", "neutral").strip().lower()
        if text:
            return text, _safe_emotion(emotion)
    except Exception:
        pass

    # Step 6: replace single quotes → double quotes and retry
    try:
        fixed = json_str.replace("'", '"')
        data = json.loads(fixed)
        text    = data.get("text", "").strip()
        emotion = data.get("emotion", "neutral").strip().lower()
        if text:
            return text, _safe_emotion(emotion)
    except Exception:
        pass

    # Step 7: regex fallback — pull value after "text":
    text_match = re.search(r'["\']?text["\']?\s*:\s*["\'](.+?)["\']', raw, re.DOTALL)
    emo_match  = re.search(r'["\']?emotion["\']?\s*:\s*["\'](\w+)["\']', raw)
    if text_match:
        return text_match.group(1).strip(), _safe_emotion(emo_match.group(1) if emo_match else "neutral")

    # Step 8: give up — return raw text so at least something shows
    return raw.strip(), "neutral"


def _safe_emotion(e: str) -> str:
    return e if e in ("happy", "sad", "angry", "surprised", "neutral") else "neutral"


def generate_reply(user_message: str, language: str) -> tuple[str, str]:
    lang_hint = _build_language_hint(language)
    augmented_message = f"{user_message}\n\n[{lang_hint}]"

    print(f"[llm] Sending to {_MODEL}: {user_message[:80]!r}")

    try:
        response = ollama.chat(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": augmented_message},
            ],
            options={
                "temperature": 0.3,   # lowered: less creative = more format-consistent
                "num_predict": 45,    # slightly more room so JSON isn't cut off
                "num_thread":  8,
                "top_k": 10,
                "top_p": 0.9,
            },
        )
        raw_content = response["message"]["content"].strip()
        print(f"[llm] Raw output: {raw_content[:200]!r}")

        reply, emotion = _parse_llm_output(raw_content)

    except Exception as e:
        print(f"[llm] ERROR: {e}")
        reply   = "I'm sorry, I can't connect to my AI brain right now."
        emotion = "sad"

    print(f"[llm] Aishwarya ({emotion}): {reply[:120]!r}")
    return reply, emotion


def _build_language_hint(language: str) -> str:
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