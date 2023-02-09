from rest_framework import serializers

from research.models import ResearcherVisit


class ResearcherVisitListSerializer(serializers.ModelSerializer):
    researcher = serializers.SlugRelatedField(slug_field='name', read_only=True)
    check_in = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    check_out = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = ResearcherVisit
        fields = ('id', 'researcher', 'check_in', 'check_out')