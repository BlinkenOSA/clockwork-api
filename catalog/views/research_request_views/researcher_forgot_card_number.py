from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.serializers.researcher_forgot_card_number_serializer import ResearcherForgotCardNumberSerializer
from clockwork_api.mailer.email_with_template import EmailWithTemplate
from research.models import Researcher


class ResearcherForgotCardNumber(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ResearcherForgotCardNumberSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.validated_data['email']
            researcher = get_object_or_404(Researcher, email=email)

            # Email template
            mail = EmailWithTemplate(
                researcher=researcher,
                context={'researcher': researcher}
            )

            mail.send_researcher_forgot_card_number()

        return Response("ok", status=status.HTTP_201_CREATED)
