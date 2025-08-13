# apps/inbox_ai/models.py
from django.db import models

class Message(models.Model):
    SOURCE_TYPES = [
        ('whatsapp', 'WHATSAPP'),
        ('sms', 'SMS'),
        ('web', 'WEB'),
    ]
    source = models.CharField(max_length=50, choices=SOURCE_TYPES, default="whatsapp")
    external_id = models.CharField(max_length=128, unique=True)
    sender = models.CharField(max_length=128)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Prediction(models.Model):
    INQUIRY_TYPES = [
        ('booking_inquiry', 'Booking Inquiry'),
        ('checkin_help', 'Check-in Help'),
        ('payment_issue', 'Payment Issue'),
        ('complaint', 'Complaint'),
        ('chit_chat', 'Chit Chat'),
    ]

    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name="prediction")
    intent = models.CharField(max_length=64, choices=INQUIRY_TYPES)
    intent_conf = models.FloatField()
    sentiment = models.CharField(max_length=16)       # positive/neutral/negative
    sentiment_score = models.FloatField()             # -1..1
    created_at = models.DateTimeField(auto_now_add=True)
