# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class MLRConfig(AppConfig):
    name = 'mlr'

    def ready(self):
        super(MLRConfig, self).ready()
        from mlr.signals import downsync_mlr
        from mlr.signals import upsync_mlr
        from mlr.signals import check_empty_mlr
