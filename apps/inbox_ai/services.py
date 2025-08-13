import joblib, os
from textblob import TextBlob  # simple sentiment (-1..1 approx)
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, "models/intent_clf.joblib")
_intent_model = None

def load_model():
    global _intent_model
    if _intent_model is None:
        _intent_model = joblib.load(MODEL_PATH)
    return _intent_model

def predict_intent_and_sentiment(text: str):
    model = load_model()
    # intent
    probs = model.predict_proba([text])[0]
    idx = probs.argmax()
    intent = model.classes_[idx]
    intent_conf = float(probs[idx])
    # sentiment (quick baseline)
    s = TextBlob(text).sentiment.polarity  # -1..1
    sentiment = "positive" if s > 0.2 else "negative" if s < -0.2 else "neutral"
    return intent, intent_conf, sentiment, float(s)