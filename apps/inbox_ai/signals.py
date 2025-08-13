from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
from .tasks import predict_for_message

@receiver(post_save, sender=Message)
def _kick_prediction(sender, instance, created, **kwargs):
    if created:
        predict_for_message.delay(instance.id)