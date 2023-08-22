from rest_framework.generics import CreateAPIView

from catalog.serializers.researcher_serializer import ResearcherSerializer
from clockwork_api.mailer.email_with_template import EmailWithTemplate
from research.models import Researcher


class ResearcherRegistration(CreateAPIView):
    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer
    permission_classes = []

    def perform_create(self, serializer):
        researcher = serializer.save()

        # Send out admin email.
        mail = EmailWithTemplate(
            researcher=researcher,
            context={'researcher': researcher}
        )
        mail.send_new_user_registration_user()
        mail.send_new_user_registration_admin()
