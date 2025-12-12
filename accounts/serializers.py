from django.contrib.auth.models import User
from rest_framework import serializers


class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Serializer for returning information about the currently authenticated user.

    Exposes:
        - Basic identity (username, first/last name, email)
        - Group membership (Group name)
        - `is_admin`: indicates whether the user is a superuser

    This serializer is typically used for “/me” endpoints or anywhere
    the front-end needs the current user's profile context.
    """
    is_admin = serializers.SerializerMethodField(read_only=True)
    groups = serializers.SlugRelatedField(many=True, slug_field='name', read_only=True)

    def get_is_admin(self, obj: User) -> bool:
        """
        Returns whether the user has superuser privileges.

        Args:
            obj: The user instance.

        Returns:
            True if the user is a superuser, otherwise False.
        """
        return obj.is_superuser

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'groups', 'is_admin')
