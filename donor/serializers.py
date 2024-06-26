from rest_framework import serializers

from authority.models import Country
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from donor.models import Donor


class DonorWriteSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
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


class DonorReadSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = '__all__'
        validators = []


class DonorListSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    is_removable = serializers.BooleanField()
    country = serializers.SlugRelatedField(slug_field='country', queryset=Country.objects.all())

    class Meta:
        model = Donor
        fields = ['id', 'name', 'country', 'city', 'address', 'email', 'is_removable']
        validators = []


class DonorSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donor
        fields = ('id', 'name')