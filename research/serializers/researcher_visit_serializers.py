from rest_framework import serializers

from research.models import ResearcherVisit


class ResearcherVisitListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing researcher visit records.

    Provides a formatted representation of :class:`research.models.ResearcherVisit`
    entries, including researcher identity, contact information, card number,
    and standardized check-in/check-out timestamps.
    """

    researcher = serializers.SlugRelatedField(slug_field='name', read_only=True)
    email = serializers.CharField(source='researcher.email', read_only=True)
    card_number = serializers.SerializerMethodField()
    check_in = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    check_out = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    def get_card_number(self, obj):
        """
        Returns the researcher's card number padded to six digits.
        """
        return "%06d" % obj.researcher.card_number

    class Meta:
        model = ResearcherVisit
        fields = ('id', 'researcher', 'email', 'card_number', 'check_in', 'check_out')
