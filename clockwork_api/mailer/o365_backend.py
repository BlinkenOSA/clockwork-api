"""Project-specific extensions to the django-o365mail backend."""

from django_o365mail import settings, util
from django_o365mail.backend import O365EmailBackend


class EmailBackend(O365EmailBackend):
    """Send Django messages through O365, including their Reply-To header.

    django-o365mail 1.1.0 does not copy ``EmailMessage.reply_to`` to the
    corresponding O365 message property. This override retains the upstream
    behavior while adding that missing mapping.
    """

    def _send(self, email_message):
        if not email_message.recipients():
            return False

        message = self.mailbox.new_message()
        message.to.add(email_message.to)
        message.cc.add(email_message.cc)
        message.bcc.add(email_message.bcc)
        message.reply_to.add(email_message.reply_to)

        message.sender.name, message.sender.address = util.get_name_and_email(
            email_message.from_email
        )
        message.subject = "".join(
            [settings.O365_SUBJECT_PREFIX, email_message.subject]
        )
        message.body = util.get_message_body(email_message)

        if email_message.attachments:
            for attachment in email_message.attachments:
                converter = util.get_converter(attachment)(attachment)
                file = converter.get_file()
                filename = converter.get_filename()

                attachment_count = len(message.attachments)
                message.attachments.add([(file, filename)])
                attachment_object = message.attachments[attachment_count]

                attachment_object.is_inline = converter.is_inline()
                attachment_object.content_id = converter.get_content_id()

        try:
            should_send = (
                settings.DEBUG and settings.O365_ACTUALLY_SEND_IN_DEBUG
            ) or not settings.DEBUG
            if should_send:
                return message.send(
                    save_to_sent_folder=settings.O365_MAIL_SAVE_TO_SENT
                )
            return True
        except Exception:
            if self.fail_silently:
                return False
            raise
