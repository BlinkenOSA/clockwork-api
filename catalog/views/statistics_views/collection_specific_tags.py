from rest_framework.response import Response
from rest_framework.views import APIView

from controlled_list.models import Keyword


class CollectionSpecificTags(APIView):
    permission_classes = []

    def get(self, *args, **kwargs):
        keywords = []
        for keyword in Keyword.objects.filter(
            findingaidsentity__published=True
        ).order_by('?').distinct():
            if len(keywords) < 10:
                if str(keyword) not in keywords:
                    keywords.append(str(keyword))
        return Response(keywords)