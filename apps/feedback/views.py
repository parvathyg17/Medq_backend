from rest_framework import generics, views, status, permissions
from rest_framework.response import Response
from .models import ContactMessage
from .serializers import ContactMessageSerializer


class ContactMessageSubmitView(generics.CreateAPIView):
    """
    POST /api/contact/submit
    Submits a customer feedback or inquiry message.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ContactMessageSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Message received successfully!"}, status=status.HTTP_200_OK)


class ContactMessageListView(generics.ListAPIView):
    """
    GET /api/contact/all
    Admin report list of all contact inquiries.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ContactMessageSerializer
    queryset = ContactMessage.objects.all()


class ChatAssistantView(views.APIView):
    """
    POST /api/feedback/chat/
    Intelligent response generation for the MedQ Virtual Assistant.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        query = request.data.get('query', '').strip().lower()

        if not query:
            return Response({
                "reply": "Hello! I am your MedQ Medical Equipment assistant. How can I assist you with clinical equipment, diagnostics, or shipping today?",
                "options": ["Warranty Info", "Shipping & Delivery", "Diagnostic Products", "Order Status"]
            })

        if "warranty" in query:
            return Response({
                "reply": "All certified MedQ equipment includes a 1-year standard manufacturer warranty covering parts and labor. Extended 3-year biomedical service warranties are available on diagnostic scanners.",
                "options": ["Claim warranty", "Service contracts", "Diagnostic Equipment"]
            })
        elif "delivery" in query or "shipping" in query:
            return Response({
                "reply": "We offer standard insured express delivery across all clinics and hospitals in 3-5 business days. Real-time temperature control is maintained for sensitive diagnostic sensors.",
                "options": ["Track order", "Delivery charges", "Bulk procurement"]
            })
        elif "diagnostic" in query or "ultrasound" in query or "monitor" in query:
            return Response({
                "reply": "Our top diagnostic catalog includes Clinical Digital Thermometers, High-Precision BP Monitors, Digital Pulse Oximeters, and Ultrasound Systems. All units carry CE and ISO medical safety certifications.",
                "options": ["Browse Diagnostic Equipment", "Request Quote", "Talk to Specialist"]
            })
        elif "return" in query or "refund" in query:
            return Response({
                "reply": "Unopened, non-sterile medical devices can be returned within 30 days of delivery. For damaged biomedical equipment, report within 48 hours for immediate replacement.",
                "options": ["Return Policy", "Contact Support"]
            })
        else:
            return Response({
                "reply": "Thank you for reaching out to MedQ Clinical Support. A certified medical equipment specialist is reviewing your inquiry.",
                "options": ["Product Specifications", "Track Order", "Leave a Message"]
            })
