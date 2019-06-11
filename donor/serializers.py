from rest_framework import serializers

from donor.models import Donor


class DonorSerializer(serializers.ModelSerializer):
    def validate(self, data):
        first_name = data.get('first_name', None)
        corporation_name = data.get('corporation_name', None)

        if not first_name and not corporation_name:
            raise serializers.ValidationError("Name or Corporation Name is mandatory!")
        else:
            return data

    class Meta:
        model = Donor
        fields = '__all__'
        validators = []


class DonorSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = ('id', 'name')