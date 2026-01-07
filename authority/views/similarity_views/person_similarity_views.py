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
    """
    Returns persons similar to a given Person record.

    This endpoint uses the internal similarity engine to find potential
    duplicates or closely related authority records based on name
    similarity.

    Permissions:
        - Read-only access allowed to unauthenticated users
        - Authentication recommended for administrative workflows
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk: int) -> Response:
        """
        Retrieves similar Person records for a given Person ID.

        Query parameters:
            limit:
                Maximum number of results to return (default: 10)

            min_similarity:
                Minimum similarity threshold on a 0–1 scale (default: 0.2)

            max_candidates:
                Maximum number of candidates evaluated (default: 5000)

            max_hamming:
                Maximum SimHash Hamming distance (default: 8)

        Args:
            request:
                HTTP request object.

            pk:
                Primary key of the target Person.

        Returns:
            HTTP 200 with a list of similar persons, each including
            a similarity percentage.
        """

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
    """
    Merges two Person authority records into one.

    This operation is destructive:
        - One Person record is kept
        - The other is deleted
        - All references are reassigned atomically

    Intended for administrative deduplication workflows.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request) -> Response:
        """
        Merges one Person record into another.

        Request body:
            keep_id:
                ID of the Person record to keep.

            merge_id:
                ID of the Person record to merge and delete.

        Behavior:
            - Reassigns all subject relationships (M2M)
            - Reassigns all associated-person relationships (FK)
            - Deletes the merged Person
            - Executes inside a single database transaction

        Returns:
            HTTP 200 on success with merge details.
            HTTP 400 for invalid input.
            HTTP 404 if one or both persons are not found.
            HTTP 500 for unexpected errors (transaction rolled back).
        """

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