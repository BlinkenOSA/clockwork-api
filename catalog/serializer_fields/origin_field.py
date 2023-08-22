import requests
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class OriginField(serializers.CharField):
    def to_internal_value(self, value):
        origin_values = {
            'Archives': 'FA',
            'Library': 'L',
            'Film Library': 'FL'
        }
        if value not in origin_values:
            raise ValidationError('Invalid value!')

        return origin_values[value]
