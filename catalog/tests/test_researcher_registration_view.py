from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from catalog.serializers.researcher_serializer import ResearcherSerializer
from catalog.views.research_request_views.researcher_registration import ResearcherRegistration


class ResearcherRegistrationViewTests(SimpleTestCase):
    def test_view_configuration(self):
        self.assertIs(ResearcherRegistration.serializer_class, ResearcherSerializer)
        self.assertEqual(ResearcherRegistration.permission_classes, [])

    def test_perform_create_saves_researcher_and_sends_both_emails(self):
        researcher = SimpleNamespace(id=1, email="new@example.com")
        serializer = Mock()
        serializer.save.return_value = researcher

        mail = SimpleNamespace(
            send_new_user_registration_user=Mock(),
            send_new_user_registration_admin=Mock(),
        )

        view = ResearcherRegistration()

        with patch(
            "catalog.views.research_request_views.researcher_registration.EmailWithTemplate",
            return_value=mail,
        ) as mock_mail_cls:
            view.perform_create(serializer)

        serializer.save.assert_called_once_with()
        mock_mail_cls.assert_called_once_with(
            researcher=researcher,
            context={"researcher": researcher},
        )
        mail.send_new_user_registration_user.assert_called_once()
        mail.send_new_user_registration_admin.assert_called_once()
