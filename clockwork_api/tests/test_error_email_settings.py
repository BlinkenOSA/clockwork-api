from django.test import SimpleTestCase

from clockwork_api.settings_components.email import (
    build_error_email_logging,
    parse_admins,
)


class ErrorEmailSettingsTests(SimpleTestCase):
    def test_parse_admins_supports_named_and_unnamed_addresses(self):
        admins = parse_admins("Josh <josh@example.com>, ops@example.com")

        self.assertEqual(
            admins,
            (
                ("Josh", "josh@example.com"),
                ("ops@example.com", "ops@example.com"),
            ),
        )

    def test_parse_admins_ignores_empty_values(self):
        self.assertEqual(parse_admins(""), ())

    def test_build_error_email_logging_sets_mail_admins_handlers(self):
        logging_config = build_error_email_logging(
            {
                "celery": {
                    "level": "WARNING",
                },
            }
        )

        self.assertEqual(
            logging_config["handlers"]["mail_admins"]["class"],
            "django.utils.log.AdminEmailHandler",
        )
        self.assertEqual(
            logging_config["handlers"]["mail_admins"]["filters"],
            ["require_debug_false"],
        )
        self.assertEqual(
            logging_config["loggers"]["django.request"]["handlers"],
            ["mail_admins"],
        )
        self.assertEqual(logging_config["loggers"]["celery"]["level"], "WARNING")
