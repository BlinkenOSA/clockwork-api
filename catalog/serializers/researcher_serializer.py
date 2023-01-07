from rest_framework import serializers
from research.models import Researcher


class ResearcherSerializer(serializers.ModelSerializer):
    captcha = serializers.CharField(read_only=True)

    class Meta:
        model = Researcher
        fields = '__all__'
