from rest_framework import serializers

from authority.models import Country
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from donor.models import Donor


class DonorWriteSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Write serializer for donor records.

    Enforces basic donor identity validation:
        - at least one of `first_name` or `corporation_name` must be provided

    User metadata behavior is applied via UserDataSerializerMixin.
    """

    def validate(self, data):
        """
        Validates donor identity fields.

        Requires either a personal first name or a corporation name. This mirrors
        the model's name derivation rules and prevents creating empty-name donors.
        """
        first_name = data.get('first_name', None)
        corporation_name = data.get('corporation_name', None)

        if not first_name and not corporation_name:
            raise serializers.ValidationError("First Name or Corporation Name is mandatory!")
        else:
            return data

    class Meta:
        model = Donor
        fields = '__all__'
        validators = []


class DonorReadSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    Read serializer for donor records.

    Exposes the full donor model for retrieval and detail views.
    User metadata behavior is applied via UserDataSerializerMixin.
    """

    class Meta:
        model = Donor
        fields = '__all__'
        validators = []


class DonorListSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
    """
    List serializer for donor records.

    Provides a compact representation for list views, including:
        - a human-readable country value
        - an `is_removable` flag for deletion-aware UIs
    """

    is_removable = serializers.BooleanField()
    country = serializers.SlugRelatedField(slug_field='country', queryset=Country.objects.all())

    class Meta:
        model = Donor
        fields = ['id', 'name', 'country', 'city', 'address', 'email', 'is_removable']
        validators = []


class DonorSelectSerializer(serializers.ModelSerializer):
    """
    Selection serializer for donor records.

    Used for lightweight lookups and UI selection widgets.
    """

    class Meta:
        model = Donor
        fields = ('id', 'name')