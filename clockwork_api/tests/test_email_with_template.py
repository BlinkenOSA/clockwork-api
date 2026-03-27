from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from clockwork_api.mailer.email_with_template import EmailWithTemplate


@override_settings(
    RESEARCH_ROOM_STAFF_EMAIL=["staff1@example.com", "staff2@example.com"],
    RESTRICTED_DECISION_MAKER_EMAIL=["decision@example.com"],
)
class EmailWithTemplateTests(SimpleTestCase):
    def _mailer(self):
        researcher = SimpleNamespace(email="user@example.com")
        return EmailWithTemplate(researcher=researcher, context={"x": 1})

    def test_send_mail_routes_to_user_and_sends_html(self):
        mailer = self._mailer()
        mailer.template = "new_request_user"

        template = Mock()
        template.render.return_value = "<p>hello</p>"

        message = Mock()
        message.send.return_value = 1

        with patch("clockwork_api.mailer.email_with_template.get_template", return_value=template) as mock_get_template, patch(
            "clockwork_api.mailer.email_with_template.EmailMessage",
            return_value=message,
        ) as mock_email_message:
            result = mailer._send_mail("user")

        self.assertEqual(result, 1)
        mock_get_template.assert_called_once_with("research/emails/new_request_user.html")
        template.render.assert_called_once_with({"x": 1})

        mock_email_message.assert_called_once_with(
            subject="Request confirmation",
            body="<p>hello</p>",
            from_email="no-reply <blinken-osa-ams@ceu.edu>",
            to=["user@example.com"],
        )
        self.assertEqual(message.content_subtype, "html")
        message.send.assert_called_once_with()

    def test_send_mail_routes_to_restricted_decision_maker(self):
        mailer = self._mailer()
        mailer.template = "new_request_restricted_decision_maker"

        template = Mock()
        template.render.return_value = "body"
        message = Mock()
        message.send.return_value = 1

        with patch("clockwork_api.mailer.email_with_template.get_template", return_value=template), patch(
            "clockwork_api.mailer.email_with_template.EmailMessage",
            return_value=message,
        ) as mock_email_message:
            mailer._send_mail("restricted_decision_maker")

        self.assertEqual(mock_email_message.call_args.kwargs["to"], ["decision@example.com"])

    def test_send_mail_routes_to_admin_for_other_targets(self):
        mailer = self._mailer()
        mailer.template = "new_request_admin"

        template = Mock()
        template.render.return_value = "body"
        message = Mock()
        message.send.return_value = 1

        with patch("clockwork_api.mailer.email_with_template.get_template", return_value=template), patch(
            "clockwork_api.mailer.email_with_template.EmailMessage",
            return_value=message,
        ) as mock_email_message:
            mailer._send_mail("admin")

        self.assertEqual(mock_email_message.call_args.kwargs["to"], ["staff1@example.com", "staff2@example.com"])

    def test_get_subject_mapping_and_unknown_template(self):
        mailer = self._mailer()

        cases = {
            "researcher_registration_admin": "New researcher registration",
            "researcher_registration_user": "Registration completed!",
            "researcher_approved_user": "Registration approved!",
            "researcher_forgot_card_number": "Your Research Card number",
            "new_request_admin": "New request arrived!",
            "new_request_user": "Request confirmation",
            "new_request_restricted_decision_maker": "New request with restricted content arrived!",
            "new_request_restricted_decision_user": "Decision about requesting restricted content!",
            "new_request_restricted_decision_admin": "Decision about requesting restricted content!",
            "request_delivered_user": "Requested items are prepared",
        }

        for template_name, expected in cases.items():
            mailer.template = template_name
            self.assertEqual(mailer._get_subject(), expected)

        mailer.template = "unknown_template"
        self.assertIsNone(mailer._get_subject())

    def test_public_methods_set_template_and_target_group(self):
        mailer = self._mailer()

        methods_and_calls = [
            ("send_new_user_registration_admin", "researcher_registration_admin", "admin"),
            ("send_new_user_registration_user", "researcher_registration_user", "user"),
            ("send_new_user_approved_user", "researcher_approved_user", "user"),
            ("send_new_request_admin", "new_request_admin", "admin"),
            ("send_new_request_user", "new_request_user", "user"),
            ("send_new_request_restricted_decision_maker", "new_request_restricted_decision_maker", "restricted_decision_maker"),
            ("send_new_request_restricted_decision_user", "new_request_restricted_decision_user", "user"),
            ("send_new_request_restricted_decision_admin", "new_request_restricted_decision_admin", "admin"),
            ("send_request_delivered_user", "request_delivered_user", "user"),
            ("send_researcher_forgot_card_number", "researcher_forgot_card_number", "user"),
        ]

        with patch.object(mailer, "_send_mail") as mock_send_mail:
            for method_name, template_name, target in methods_and_calls:
                getattr(mailer, method_name)()
                self.assertEqual(mailer.template, template_name)
                self.assertEqual(mock_send_mail.call_args_list[-1].args, (target,))
