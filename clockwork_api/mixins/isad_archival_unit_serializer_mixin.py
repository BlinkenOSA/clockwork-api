class IsadArchivalUnitSerializerMixin:
    """
    Serializer mixin for exposing ISAD(G) publication status on ArchivalUnit objects.

    This mixin provides a reusable `get_status()` method that determines the
    descriptive status of an archival unit based on the existence and
    publication state of its related ISAD(G) record.

    It is intended for use in DRF serializers that represent archival units
    within the ISAD module hierarchy (fonds, subfonds, series).

    Status Logic:
        - If no related ISAD record exists:
              → "Not exists"

        - If an ISAD record exists and is unpublished:
              → "Draft"

        - If an ISAD record exists and is published:
              → "Published"

    This enables consistent status labeling across list, tree, and detail
    views in the archival description interface.

    Typical Usage:
        class IsadSeriesSerializer(
            IsadArchivalUnitSerializerMixin,
            serializers.ModelSerializer
        ):
            status = serializers.SerializerMethodField()

            def get_status(self, obj):
                return super().get_status(obj)

    Example Output:
        {
            "id": 42,
            "reference_code": "HU OSA 386-1-1",
            "title": "Political Files",
            "status": "Published"
        }
    """

    def get_status(self, obj) -> str:
        """
        Return the ISAD(G) publication status for an archival unit.

        Args:
            obj (ArchivalUnit):
                The archival unit instance being serialized.

        Returns:
            str:
                One of the following values:

                - "Published"  → ISAD exists and is published
                - "Draft"      → ISAD exists but is unpublished
                - "Not exists" → No related ISAD record exists
        """
        if hasattr(obj, 'isad'):
            return 'Published' if obj.isad.published else 'Draft'
        else:
            return 'Not exists'
