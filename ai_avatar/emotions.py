"""
emotions.py — Keyword → Avatar Emotion Mapper
=============================================
Responsibilities:
  - Scan the LLM reply text for emotional keywords
  - Return a dict of morph-target weights to apply to the avatar
  - Supports: happy, sad, angry, surprised, neutral

Avatar emotion morph targets (from spec):
  mouthSmile
  mouthFrownLeft, mouthFrownRight
  browDownLeft, browDownRight
  browInnerUp
  eyeWideLeft, eyeWideRight
  cheekSquintLeft, cheekSquintRight

All weights are floats 0.0 → 1.0.
The Three.js frontend lerps to these values over ~500 ms.
"""

import re

# ─────────────────────────────────────────────────────────────
# Keyword lists (lowercase; regex word-boundary matched)
# ─────────────────────────────────────────────────────────────

_HAPPY_KEYWORDS = [
    # English
    r"happy", r"great", r"wonderful", r"awesome", r"fantastic",
    r"excellent", r"love", r"congrat", r"haha", r"lol", r"sure",
    r"absolutely", r"delighted", r"glad", r"yay", r"hurray",
    r"good", r"nice", r"amazing", r"perfect", r"brilliant",
    # Hindi
    r"खुश", r"बढ़िया", r"शानदार", r"बहुत अच्छा", r"हाहाहा",
    r"वाह", r"ज़रूर", r"बिल्कुल", r"मस्त", r"क्या बात",
]

_SAD_KEYWORDS = [
    # English
    r"sorry", r"apolog", r"sad", r"unfortunate", r"regret",
    r"disappoint", r"miss", r"lost", r"grief", r"mourn",
    r"hurt", r"pain", r"difficult", r"trouble", r"problem",
    # Hindi
    r"माफ", r"दुख", r"बुरा", r"अफसोस", r"परेशान", r"तकलीफ",
]

_ANGRY_KEYWORDS = [
    r"angry", r"furious", r"annoyed", r"frustrat", r"irritat",
    r"upset", r"wrong", r"stop", r"enough", r"ridiculous",
    r"गुस्सा", r"नाराज", r"परेशान",
]

_SURPRISED_KEYWORDS = [
    r"wow", r"oh my", r"really", r"seriously", r"unexpected",
    r"surprising", r"amazing", r"incredible", r"unbelievable",
    r"no way", r"what", r"whoa",
    r"वाकई", r"सच में", r"अरे", r"ओह",
]

# ─────────────────────────────────────────────────────────────
# Emotion → morph target weights
# ─────────────────────────────────────────────────────────────

_EMOTION_WEIGHTS: dict[str, dict[str, float]] = {
    "happy": {
        "mouthSmile":       0.25,
        "cheekSquintLeft":  0.70,
        "cheekSquintRight": 0.70,
        "browInnerUp":      0.30,
        "eyeWideLeft":      0.15,
        "eyeWideRight":     0.15,
        # reset sad/angry targets
        "mouthFrownLeft":   0.00,
        "mouthFrownRight":  0.00,
        "browDownLeft":     0.00,
        "browDownRight":    0.00,
    },
    "sad": {
        "mouthFrownLeft":   0.90,
        "mouthFrownRight":  0.90,
        "browInnerUp":      0.80,
        "browDownLeft":     0.25,
        "browDownRight":    0.25,
        # reset happy targets
        "mouthSmile":       0.00,
        "cheekSquintLeft":  0.00,
        "cheekSquintRight": 0.00,
        "eyeWideLeft":      0.00,
        "eyeWideRight":     0.00,
    },
    "angry": {
        "browDownLeft":     0.80,
        "browDownRight":    0.80,
        "mouthFrownLeft":   0.40,
        "mouthFrownRight":  0.40,
        # reset
        "mouthSmile":       0.00,
        "browInnerUp":      0.00,
        "cheekSquintLeft":  0.00,
        "cheekSquintRight": 0.00,
        "eyeWideLeft":      0.00,
        "eyeWideRight":     0.00,
    },
    "surprised": {
        "eyeWideLeft":      0.90,
        "eyeWideRight":     0.90,
        "browInnerUp":      0.80,
        "mouthSmile":       0.05,
        # reset
        "mouthFrownLeft":   0.00,
        "mouthFrownRight":  0.00,
        "browDownLeft":     0.00,
        "browDownRight":    0.00,
        "cheekSquintLeft":  0.00,
        "cheekSquintRight": 0.00,
    },
    "neutral": {
        "mouthSmile":       0.00,   # NO SMILE to keep lips closed
        "mouthFrownLeft":   0.00,
        "mouthFrownRight":  0.00,
        "browDownLeft":     0.00,
        "browDownRight":    0.00,
        "browInnerUp":      0.00,
        "eyeWideLeft":      0.00,
        "eyeWideRight":     0.00,
        "cheekSquintLeft":  0.00,
        "cheekSquintRight": 0.00,
    },
}


def detect_emotion(reply_text: str, manual_emotion: str | None = None) -> dict:
    """
    Detect the dominant emotion from reply text and return
    the corresponding morph-target weight dict.

    Parameters
    ----------
    reply_text : str
        The LLM reply string (any language).
    manual_emotion : str, optional
        An emotion name provided directly by the LLM (e.g. "happy").
        If provided and valid, this overrides the keyword scan.

    Returns
    -------
    dict with keys:
      "emotion"  → detected emotion name (str)
      "weights"  → {morph_target: float, …}
    """
    if manual_emotion and manual_emotion.lower() in _EMOTION_WEIGHTS:
        best_emotion = manual_emotion.lower()
        print(f"[emotions] Using LLM provided emotion: {best_emotion}")
    else:
        text_lower = reply_text.lower()
        scores = {
            "happy":     _score(text_lower, _HAPPY_KEYWORDS),
            "sad":       _score(text_lower, _SAD_KEYWORDS),
            "angry":     _score(text_lower, _ANGRY_KEYWORDS),
            "surprised": _score(text_lower, _SURPRISED_KEYWORDS),
        }
        best_emotion = max(scores, key=scores.get)

        # Fall back to neutral if nothing matched
        if scores[best_emotion] == 0:
            best_emotion = "neutral"
        
        print(f"[emotions] Keyword detected: {best_emotion}  scores={scores}")

    return {
        "emotion": best_emotion,
        "weights": _EMOTION_WEIGHTS[best_emotion],
    }


# ─────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────

def _score(text: str, keywords: list[str]) -> int:
    """Count how many keyword patterns appear in text."""
    count = 0
    for kw in keywords:
        if re.search(kw, text, re.IGNORECASE | re.UNICODE):
            count += 1
    return count
