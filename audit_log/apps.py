# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class AuditLogConfig(AppConfig):
    name = 'audit_log'

    def ready(self):
        from . import signals
