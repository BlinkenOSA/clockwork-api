import requests
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class HCaptchaField(serializers.Field):
    def to_internal_value(self, data):
        captcha_url = getattr(settings, 'HCAPTCHA_VERIFY_URL', None)
        sitekey = getattr(settings, 'HCAPTCHA_SITE_KEY', None)

        # Check the submitted captcha
        if data:
            data = {
                'secret': sitekey,
                'response': data
            }
            r = requests.post(captcha_url, data=data)

            if r.status_code == 200:
                response = r.json()
                if not response['success']:
                    raise ValidationError('Captcha is invalid, please refresh the page!')
                else:
                    return ''
            else:
                raise ValidationError('Error communicating with HCaptcha server!')
        else:
            raise ValidationError('Captcha is required!')

    def to_representation(self, value):
        return ''
