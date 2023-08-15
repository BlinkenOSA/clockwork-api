from rest_framework.views import APIView
from catalog.serializers.research_request_serializer import ResearchRequestSerializer
from research.models import Request, Researcher


class ResearcherRequestView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ResearchRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            request = Request.objects.create(
                researcher=data['researcher'],
                request_date=data['request_date']
            )
