import contextlib
import pytest
import numpy as np
from types import SimpleNamespace
from rest_framework.test import APIRequestFactory

from inbox_ai.models import Message, Prediction
from inbox_ai import services, tasks
from inbox_ai.api import MessageViewSet
from django.db.models.signals import post_save
from inbox_ai.signals import _kick_prediction


# ---- helper: temporarily disable the post_save signal that enqueues the task
@contextlib.contextmanager
def no_autopredict_signal():
    post_save.disconnect(_kick_prediction, sender=Message)
    try:
        yield
    finally:
        post_save.connect(_kick_prediction, sender=Message)


@pytest.mark.django_db
def test_post_save_signal_triggers_task_delay(monkeypatch):
    # Ensure signals are imported/connected
    import inbox_ai.signals as inbox_signals

    called = {}

    def fake_delay(msg_id):
        called["msg_id"] = msg_id

    # Patch the *signal's* reference (it does `from .tasks import predict_for_message`)
    monkeypatch.setattr(inbox_signals.predict_for_message, "delay", fake_delay, raising=False)

    msg = Message.objects.create(
        source="whatsapp", external_id="wa_123", sender="+2348000000000", text="Is the 2-bed free this weekend?"
    )

    assert called.get("msg_id") == msg.id, "Signal should enqueue Celery task with the new message id"


@pytest.mark.django_db
def test_task_creates_prediction_row(monkeypatch):
    # Stub the ML *where the task looks it up* (in tasks namespace).
    monkeypatch.setattr(
        tasks,
        "predict_intent_and_sentiment",
        lambda text: ("booking_inquiry", 0.92, "positive", 0.55),
        raising=True,
    )

    # Don't let the signal auto-run the task; we'll call it manually.
    with no_autopredict_signal():
        msg = Message.objects.create(
            source="whatsapp",
            external_id="wa_456",
            sender="+2348111111111",
            text="Hi, is your 2-bedroom available?",
        )

    # Execute the Celery task body synchronously (no broker involved).
    tasks.predict_for_message.run(msg.id)

    pred = Prediction.objects.get(message=msg)
    assert pred.intent == "booking_inquiry"
    assert pred.intent_conf == pytest.approx(0.92, rel=1e-6)
    assert pred.sentiment == "positive"
    assert pred.sentiment_score == pytest.approx(0.55, rel=1e-6)


@pytest.mark.django_db
def test_services_predict_intent_and_sentiment(monkeypatch):
    # Fake model returned by services.load_model()
    class FakeModel:
        def __init__(self):
            self.classes_ = np.array(["booking_inquiry", "complaint"])
        def predict_proba(self, X):
            # Highest prob on index 0 => "booking_inquiry"
            return np.array([[0.9, 0.1]])

    monkeypatch.setattr(services, "load_model", lambda: FakeModel())

    # Stub TextBlob sentiment inside services
    monkeypatch.setattr(
        services,
        "TextBlob",
        lambda t: SimpleNamespace(sentiment=SimpleNamespace(polarity=0.6)),
    )

    intent, conf, sentiment, score = services.predict_intent_and_sentiment("Great place, thanks!")
    assert intent == "booking_inquiry"
    assert conf == pytest.approx(0.9, rel=1e-6)
    assert sentiment == "positive"
    assert score == pytest.approx(0.6, rel=1e-6)


@pytest.mark.django_db
def test_insight_endpoint_pending_when_no_prediction():
    factory = APIRequestFactory()
    view = MessageViewSet.as_view({"get": "insight"})

    # Prevent the signal from creating a Prediction automatically.
    with no_autopredict_signal():
        msg = Message.objects.create(
            source="whatsapp",
            external_id="wa_789",
            sender="+2348222222222",
            text="How do I check in?",
        )

    req = factory.get(f"/messages/{msg.pk}/insight/")
    resp = view(req, pk=str(msg.pk))
    assert resp.status_code == 200
    assert resp.data == {"status": "pending"}


@pytest.mark.django_db
def test_insight_endpoint_with_prediction():
    from inbox_ai import replies

    factory = APIRequestFactory()
    view = MessageViewSet.as_view({"get": "insight"})

    # Avoid the signal running the model loader; we'll create Prediction ourselves.
    with no_autopredict_signal():
        msg = Message.objects.create(
            source="whatsapp",
            external_id="wa_900",
            sender="+2348333333333",
            text="I was charged twice!",
        )

    Prediction.objects.create(
        message=msg,
        intent="payment_issue",
        intent_conf=0.88,
        sentiment="negative",
        sentiment_score=-0.4,
    )

    req = factory.get(f"/messages/{msg.pk}/insight/")
    resp = view(req, pk=str(msg.pk))
    assert resp.status_code == 200
    assert resp.data["intent"] == "payment_issue"
    assert resp.data["confidence"] == pytest.approx(0.88, rel=1e-6)
    assert resp.data["sentiment"] == "negative"
    assert isinstance(resp.data["suggestions"], list)
    assert resp.data["suggestions"][0] in replies.SUGGESTIONS["payment_issue"]