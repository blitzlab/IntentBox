from celery import shared_task
from django.db import transaction
from inbox_ai.models import Message, Prediction
from inbox_ai.services import predict_intent_and_sentiment

@shared_task(max_retries=2, default_retry_delay=60)
def predict_for_message(message_id: int):
    msg = Message.objects.get(id=message_id)
    intent, conf, senti, score = predict_intent_and_sentiment(msg.text)
    with transaction.atomic():
        Prediction.objects.update_or_create(
            message=msg,
            defaults=dict(intent=intent, intent_conf=conf, sentiment=senti, sentiment_score=score)
        )