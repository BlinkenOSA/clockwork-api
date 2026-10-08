from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django_o365mail import settings

from clockwork_api.mailer.o365_backend import EmailBackend


class O365EmailBackendTests(SimpleTestCase):
    def test_send_copies_reply_to_to_o365_message(self):
        backend = object.__new__(EmailBackend)
        backend.fail_silently = False

        o365_message = Mock()
        o365_message.sender = SimpleNamespace(name=None, address=None)
        o365_message.send.return_value = True
        backend.mailbox = Mock()
        backend.mailbox.new_message.return_value = o365_message

        email_message = Mock()
        email_message.recipients.return_value = ["user@example.com"]
        email_message.to = ["user@example.com"]
        email_message.cc = []
        email_message.bcc = []
        email_message.reply_to = ["research-room@example.com"]
        email_message.from_email = "Clockwork <no-reply@example.com>"
        email_message.subject = "Subject"
        email_message.attachments = []

        with patch(
            "clockwork_api.mailer.o365_backend.util.get_message_body",
            return_value="Body",
        ), patch("clockwork_api.mailer.o365_backend.settings.DEBUG", False):
            result = backend._send(email_message)

        self.assertTrue(result)
        o365_message.reply_to.add.assert_called_once_with(
            ["research-room@example.com"]
        )
        o365_message.send.assert_called_once_with(
            save_to_sent_folder=settings.O365_MAIL_SAVE_TO_SENT
        )
