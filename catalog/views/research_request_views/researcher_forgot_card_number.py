"""
Public endpoint for retrieving a researcher's card number via email.

This module provides a public API endpoint that allows a researcher
to request their card number by submitting their registered email address.

The endpoint:
    - validates the email address format
    - looks up the associated Researcher record
    - sends the card number via email
    - does not reveal whether an email exists in the system beyond HTTP status

This functionality is intentionally unauthenticated.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.serializers.researcher_forgot_card_number_serializer import ResearcherForgotCardNumberSerializer
from clockwork_api.mailer.email_with_template import EmailWithTemplate
from research.models import Researcher


class ResearcherForgotCardNumber(APIView):
    """
    Handles forgotten researcher card number requests.

    This endpoint:
        - accepts an email address
        - validates input via serializer
        - sends the associated card number via email

    The card number is never returned in the API response.
    """
    permission_classes = []

    def post(self, request) -> Response:
        """
        Processes a researcher card number recovery request.

        Expected request payload:
            - email:
                Primary email address associated with the Researcher record.
            - email_confirm:
                Confirmation of the email address (must match `email`).
            - captcha:
                hCaptcha response token used for abuse prevention.

        Validation:
            - Email fields must be valid email addresses
            - `email` and `email_confirm` must match (see serializer logic)
            - hCaptcha must be successfully verified

        Behavior:
            - If validation succeeds, the Researcher record is looked up by email
            - If found, an email containing the card number is sent
            - The card number is never returned in the API response

        Returns:
            HTTP 201 with a generic success message ("ok").

        Raises:
            - ValidationError if input validation fails
            - Http404 if no Researcher exists for the provided email

        Security notes:
            - This endpoint is intentionally unauthenticated
            - Abuse prevention relies on hCaptcha and external rate limiting
            - The response does not disclose sensitive information
        """
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
