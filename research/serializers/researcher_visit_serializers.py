from rest_framework import serializers

from research.models import ResearcherVisit


class ResearcherVisitListSerializer(serializers.ModelSerializer):
    researcher = serializers.SlugRelatedField(slug_field='name', read_only=True)
    email = serializers.CharField(source='researcher.email', read_only=True)
    card_number = serializers.SerializerMethodField()
    check_in = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    check_out = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    def get_card_number(self, obj):
        return "%06d" % obj.researcher.card_number

    class Meta:
        model = ResearcherVisit
        fields = ('id', 'researcher', 'email', 'card_number', 'check_in', 'check_out')