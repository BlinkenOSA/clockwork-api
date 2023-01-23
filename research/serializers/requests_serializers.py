from rest_framework import serializers

from research.models import RequestItem


class RequestListSerializer(serializers.ModelSerializer):
    researcher = serializers.SlugRelatedField(slug_field='name', read_only=True)

    class Meta:
        model = RequestItem
        fields = '__all__'
