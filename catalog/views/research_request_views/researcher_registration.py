"""
Public researcher self-registration endpoint.

This module provides a public-facing API endpoint that allows researchers
to register themselves in the system.

Registration includes:
    - full Researcher model creation
    - mandatory hCaptcha verification
    - automatic email notifications to:
        * the researcher
        * system administrators

This endpoint is intentionally unauthenticated and rate-limited
externally (e.g. via reverse proxy).
"""
from rest_framework.generics import CreateAPIView

from catalog.serializers.researcher_serializer import ResearcherSerializer
from clockwork_api.mailer.email_with_template import EmailWithTemplate
from research.models import Researcher


class ResearcherRegistration(CreateAPIView):
    """
    Handles public researcher registration.

    This endpoint:
        - creates a new Researcher record
        - validates hCaptcha via the serializer
        - triggers notification emails upon success

    No authentication is required because this is a public registration
    endpoint. Abuse prevention relies on captcha and external rate limiting.
    """

    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer
    permission_classes = []

    def perform_create(self, serializer) -> None:
        """
        Persists a new Researcher and triggers registration emails.

        Side effects:
            - Sends confirmation email to the researcher
            - Sends notification email to administrators

        Args:
            serializer:
                Validated ResearcherSerializer instance.
        """
        researcher = serializer.save()

        # Send out admin email.
        mail = EmailWithTemplate(
            researcher=researcher,
            context={'researcher': researcher}
        )
        mail.send_new_user_registration_user()
        mail.send_new_user_registration_admin()
