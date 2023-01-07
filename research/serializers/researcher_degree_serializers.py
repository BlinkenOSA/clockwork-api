from rest_framework import serializers
from research.models import ResearcherDegree


class ResearcherDegreeReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearcherDegree
        fields = '__all__'


class ResearcherDegreeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearcherDegree
        fields = '__all__'


class ResearcherDegreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearcherDegree
        fields = ('id', 'degree')

