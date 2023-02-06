import requests
from django.conf import settings
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK

from catalog.serializers.researcher_serializer import ResearcherSerializer
from research.models import Researcher


class ResearcherRegistration(CreateAPIView):
    queryset = Researcher.objects.all()
    serializer_class = ResearcherSerializer
    permission_classes = []

    def create(self, request, *args, **kwargs):
        captcha_token = request.data.get('captcha', None)
        captcha_url = getattr(settings, 'HCAPTCHA_VERIFY_URL', None)
        sitekey = getattr(settings, 'HCAPTCHA_SITE_KEY', None)

        # Check the submitted captcha
        if captcha_token:
            data = {
                'secret': sitekey,
                'response': captcha_token
            }
            r = requests.post(captcha_url, data=data)

            if r.status_code == 200:
                response = r.json()
                if response['success']:
                    super(ResearcherRegistration, self).create(request)
                    return Response(data={'message': 'We received your registration! Our colleagues are validating '
                                                     'your submitted data, and get back to you once the registration '
                                                     'is approoved!'}, status=HTTP_200_OK)
                else:
                    return Response(data={'message': 'Captcha is invalid, please refresh the page!'},
                                    status=HTTP_400_BAD_REQUEST)
            else:
                return Response(status=r.status_code)
        else:
            return Response(data={'message': 'Captcha is missing.'}, status=HTTP_400_BAD_REQUEST)