from rest_framework import serializers

from authority.serializers import CountrySelectSerializer
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from donor.models import Donor


class DonorSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    country = CountrySelectSerializer()

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