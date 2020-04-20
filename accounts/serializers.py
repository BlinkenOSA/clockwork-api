from django.contrib.auth.models import User
from rest_framework import serializers


class CurrentUserSerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField(read_only=True)
    groups = serializers.SlugRelatedField(many=True, slug_field='name', read_only=True)

    def get_is_admin(self, obj):
        return obj.is_superuser

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'groups', 'is_admin')
