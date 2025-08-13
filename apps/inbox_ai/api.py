from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from inbox_ai.models import Message
from inbox_ai.replies import suggestions_for_intent

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().select_related("prediction").order_by("-created_at")
    serializer_class = MessageSerializer

    @action(detail=True, methods=["get"])
    def insight(self, request, pk=None):
        msg = self.get_object()
        pred = getattr(msg, "prediction", None)
        if not pred:
            return Response({"status":"pending"})
        return Response({
            "intent": pred.intent,
            "confidence": pred.intent_conf,
            "sentiment": pred.sentiment,
            "sentiment_score": pred.sentiment_score,
            "suggestions": suggestions_for_intent(pred.intent),
        })