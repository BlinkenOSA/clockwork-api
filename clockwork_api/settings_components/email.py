import os
from email.utils import getaddresses


def parse_admins(value):
    if isinstance(value, (list, tuple)):
        return tuple((name or address, address) for name, address in value if address)

    return tuple(
        (name or address, address)
        for name, address in getaddresses([value])
        if address
    )


def build_error_email_logging(extra_loggers=None):
    loggers = {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "celery": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
        },
        "celery.app.trace": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
        },
    }

    if extra_loggers:
        loggers.update(extra_loggers)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "require_debug_false": {
                "()": "django.utils.log.RequireDebugFalse",
            },
        },
        "handlers": {
            "mail_admins": {
                "level": "ERROR",
                "filters": ["require_debug_false"],
                "class": "django.utils.log.AdminEmailHandler",
                "include_html": True,
            },
        },
        "loggers": loggers,
    }


EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django_o365mail.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DJANGO_DEFAULT_FROM_EMAIL",
    "no-reply <blinken-osa-ams@ceu.edu>",
)
SERVER_EMAIL = os.environ.get("DJANGO_SERVER_EMAIL", DEFAULT_FROM_EMAIL)
EMAIL_SUBJECT_PREFIX = os.environ.get(
    "DJANGO_EMAIL_SUBJECT_PREFIX",
    "[Clockwork API] ",
)

# `local.py` can override this directly with Django's native tuple-of-tuples
# format, while env-based deployments can continue to use `DJANGO_ADMINS`.
ADMINS = parse_admins(globals().get("ADMINS", os.environ.get("DJANGO_ADMINS", "")))
MANAGERS = ADMINS

O365_MAIL_CLIENT_ID = os.environ.get("O365_MAIL_CLIENT_ID")
O365_MAIL_CLIENT_SECRET = os.environ.get("O365_MAIL_CLIENT_SECRET")
O365_MAIL_TENANT_ID = os.environ.get("O365_MAIL_TENANT_ID")

o365_mailbox_resource = os.environ.get("O365_MAIL_MAILBOX_RESOURCE")
O365_MAIL_MAILBOX_KWARGS = (
    {"resource": o365_mailbox_resource}
    if o365_mailbox_resource
    else {}
)
O365_SUBJECT_PREFIX = os.environ.get(
    "O365_SUBJECT_PREFIX",
    EMAIL_SUBJECT_PREFIX,
)
O365_ACTUALLY_SEND_IN_DEBUG = os.environ.get(
    "O365_ACTUALLY_SEND_IN_DEBUG",
    "",
).lower() in {"1", "true", "yes", "on"}

LOGGING = build_error_email_logging()
