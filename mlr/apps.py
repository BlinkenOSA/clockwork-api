# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class MLRConfig(AppConfig):
    """
    Application configuration for the MLR (Master Location Register) app.

    The MLR app manages master location register data and keeps it synchronized
    with related systems via Django signals.

    The ``ready`` hook imports signal handlers to ensure they are registered
    when the application is loaded.
    """

    name = 'mlr'

    def ready(self):
        """
        Imports signal handlers for the MLR app.

        This method is called when the Django application registry is fully
        populated. Importing these modules here ensures that all signal
        receivers are registered at startup.
        """
        super(MLRConfig, self).ready()
        from mlr.signals import downsync_mlr
        from mlr.signals import upsync_mlr
        from mlr.signals import check_empty_mlr
