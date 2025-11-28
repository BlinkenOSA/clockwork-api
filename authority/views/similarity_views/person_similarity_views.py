# myapp/api/views.py
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from authority.models import Person
from authority.serializers import SimilarPersonSerializer
from authority.similarity import similar_people
from finding_aids.models import FindingAidsEntity, FindingAidsEntityAssociatedPerson


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


class PersonSimilarMerge(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request):
        keep_id = request.data.get("keep_id")
        merge_id = request.data.get("merge_id")

        if not keep_id or not merge_id:
            return Response({"error": "keep_id and merge_id are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        if keep_id == merge_id:
            return Response({"error": "keep_id and merge_id must be different."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                person_keep = Person.objects.get(id=keep_id)
                person_merge = Person.objects.get(id=merge_id)

                # Merge M2M
                for entity in FindingAidsEntity.objects.filter(subject_person=person_merge):
                    entity.subject_person.add(person_keep)
                    entity.subject_person.remove(person_merge)

                # Merge FK
                FindingAidsEntityAssociatedPerson.objects.filter(
                    associated_person=person_merge
                ).update(associated_person=person_keep)

                # Delete merged person
                person_merge.delete()

        except Person.DoesNotExist:
            return Response({"error": "One or both persons not found."},
                            status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # Transaction rolled back automatically
            return Response({"error": f"Unexpected error: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "message": "Merge completed successfully.",
            "keep_id": keep_id,
            "deleted_merge_id": merge_id
        })