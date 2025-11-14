# myapp/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from authority.models import Person
from authority.serializers import SimilarPersonSerializer
from authority.similarity import similar_people

class PersonSimilarById(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk: int):
        try:
            person = Person.objects.get(pk=pk)
        except Person.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        target_full = f"{person.first_name} {person.last_name}".strip()
        results = similar_people(
            target_full,
            exclude_id=person.id,
            limit=int(request.GET.get('limit', 10)),
            min_similarity=float(request.GET.get('min_similarity', 0.2)),
            max_candidates=int(request.GET.get('max_candidates', 5000)),
            max_hamming=int(request.GET.get('max_hamming', 8)),
        )
        return Response(SimilarPersonSerializer(results, many=True).data)
