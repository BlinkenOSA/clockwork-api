from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings


@override_settings(
    DEFAULT_FROM_EMAIL="Clockwork API <mailbox@example.com>",
    EMAIL_BACKEND="django_o365mail.EmailBackend",
)
class SendTestEmailCommandTests(SimpleTestCase):
    @override_settings(ADMINS=(("Josh", "josh@example.com"),))
    def test_command_uses_first_admin_when_to_not_provided(self):
        mock_connection = Mock()
        mock_message = Mock()
        mock_message.send.return_value = 1

        out = StringIO()

        with patch(
            "accounts.management.commands.send_test_email.get_connection",
            return_value=mock_connection,
        ), patch(
            "accounts.management.commands.send_test_email.EmailMessage",
            return_value=mock_message,
        ) as mock_email_message:
            call_command("send_test_email", stdout=out)

        self.assertEqual(mock_email_message.call_args.kwargs["to"], ["josh@example.com"])
        self.assertEqual(
            mock_email_message.call_args.kwargs["from_email"],
            "Clockwork API <mailbox@example.com>",
        )
        self.assertEqual(mock_email_message.call_args.kwargs["connection"], mock_connection)
        self.assertIn("Test email sent to josh@example.com", out.getvalue())

    def test_command_uses_explicit_recipient(self):
        mock_message = Mock()
        mock_message.send.return_value = 1

        with patch(
            "accounts.management.commands.send_test_email.get_connection",
            return_value=Mock(),
        ), patch(
            "accounts.management.commands.send_test_email.EmailMessage",
            return_value=mock_message,
        ) as mock_email_message:
            call_command("send_test_email", "--to", "me@example.com", "--subject", "O365 check")

        self.assertEqual(mock_email_message.call_args.kwargs["to"], ["me@example.com"])
        self.assertEqual(mock_email_message.call_args.kwargs["subject"], "O365 check")

    @override_settings(ADMINS=())
    def test_command_requires_recipient_when_admins_missing(self):
        with self.assertRaisesMessage(CommandError, "No recipient provided. Use --to or set DJANGO_ADMINS."):
            call_command("send_test_email")
