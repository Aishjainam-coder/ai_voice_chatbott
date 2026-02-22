"""
Sentiment Analysis Module
Detects emotion from text using DistilBERT (local, free) with keyword fallback.
"""

_POS = {"good","great","happy","love","excellent","amazing","wonderful",
        "fantastic","awesome","nice","glad","thanks","cool","brilliant",
        "perfect","yes","excited","fun","enjoy","laugh","joy"}
_NEG = {"bad","sad","hate","terrible","awful","horrible","worst","angry",
        "upset","disappointed","wrong","no","not","never","problem",
        "issue","error","fail","broken","scared","worried","cry","pain"}

EMOTION_MAP = {
    "positive": ["happy","excited","friendly","confident"],
    "negative": ["sad","concerned","thoughtful","empathetic"],
    "neutral":  ["calm","focused","professional","attentive"],
}

class SentimentAnalyzer:
    def __init__(self):
        self._model = None
        self._tried = False

    def _load(self):
        if self._tried: return
        self._tried = True
        try:
            import torch, transformers
            self._model = transformers.pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0 if torch.cuda.is_available() else -1)
            print("✅ Sentiment model loaded")
        except Exception as e:
            print(f"⚠ Sentiment fallback mode: {e}")

    def analyze(self, text: str) -> dict:
        if not text or not text.strip():
            return {"label":"neutral","score":0.5,"emotion":"calm"}
        self._load()
        if self._model:
            try:
                r = self._model(text[:512])[0]
                lbl = r["label"].lower()
                em  = EMOTION_MAP.get(lbl, EMOTION_MAP["neutral"])[0]
                return {"label":lbl,"score":float(r["score"]),"emotion":em}
            except: pass
        words = set(text.lower().split())
        p, n = len(words & _POS), len(words & _NEG)
        if p > n: return {"label":"positive","score":0.8,"emotion":"happy"}
        if n > p: return {"label":"negative","score":0.8,"emotion":"sad"}
        return           {"label":"neutral", "score":0.5,"emotion":"calm"}

    def get_emotion_for_response(self, user_text: str, ai_reply: str = "") -> str:
        s = self.analyze(user_text)
        if ai_reply:
            if s["label"] == "negative": return "empathetic"
            if s["label"] == "positive": return "happy"
        return s["emotion"]

    def get_emotion(self, user_text: str, ai_reply: str = "") -> str:
        return self.get_emotion_for_response(user_text, ai_reply)