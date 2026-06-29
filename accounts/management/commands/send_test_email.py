from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.core.management import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Send a test email using the configured Django email backend."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="to_email",
            help="Recipient email address. Defaults to the first address in DJANGO_ADMINS.",
        )
        parser.add_argument(
            "--subject",
            default="Clockwork API test email",
            help="Optional subject line for the test email.",
        )

    def handle(self, *args, **options):
        to_email = options["to_email"] or self._get_default_recipient()
        subject = options["subject"]
        sent_at = timezone.now().isoformat()

        message = EmailMessage(
            subject=subject,
            body=(
                "This is a Clockwork API test email sent through the configured "
                f"Django email backend at {sent_at}."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
            connection=get_connection(),
        )

        sent_count = message.send()
        if sent_count != 1:
            raise CommandError(f"Expected to send 1 email, sent {sent_count}.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Test email sent to {to_email} using {settings.EMAIL_BACKEND}."
            )
        )

    def _get_default_recipient(self):
        if settings.ADMINS:
            return settings.ADMINS[0][1]

        raise CommandError(
            "No recipient provided. Use --to or set DJANGO_ADMINS."
        )
