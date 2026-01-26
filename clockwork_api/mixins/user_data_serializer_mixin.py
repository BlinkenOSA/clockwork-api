from django.utils import timezone


class UserDataSerializerMixin:
    """
    Serializer mixin for automatic user and timestamp tracking.

    This mixin injects auditing metadata into model instances during
    create and update operations by automatically populating:

        - user_created   → Username of the creator
        - user_updated   → Username of the last editor
        - date_updated   → Timestamp of last modification

    It relies on the presence of the current request object in the
    serializer context.

    This mixin is intended for use with serializers that write to models
    containing user and date tracking fields.

    Required Model Fields:
        - user_created (CharField)
        - user_updated (CharField)
        - date_updated (DateTimeField)

    Required Serializer Context:
        {
            "request": <HttpRequest>
        }

    Typical Usage:

        class ExampleWriteSerializer(
            UserDataSerializerMixin,
            serializers.ModelSerializer
        ):
            class Meta:
                model = Example
                fields = "__all__"

    Behavior:
        - On create():
              Sets `user_created` to request.user.username

        - On update():
              Sets `user_updated` to request.user.username
              Sets `date_updated` to timezone.now()

    This ensures consistent provenance tracking across the system
    without requiring manual field management in each serializer.
    """

    def create(self, validated_data):
        """
        Create a new model instance with creator metadata.

        Automatically populates the `user_created` field using the
        authenticated user's username.

        Args:
            validated_data (dict):
                Validated serializer input data.

        Returns:
            models.Model:
                Newly created model instance.
        """
        validated_data['user_created'] = self.context['request'].user.username
        return super(UserDataSerializerMixin, self).create(validated_data)

    def update(self, instance, validated_data):
        """
        Update an existing model instance with modification metadata.

        Automatically populates:

            - user_updated
            - date_updated

        based on the current authenticated user and timestamp.

        Args:
            instance (models.Model):
                Existing model instance.

            validated_data (dict):
                Validated serializer input data.

        Returns:
            models.Model:
                Updated model instance.
        """
        validated_data['user_updated'] = self.context['request'].user.username
        validated_data['date_updated'] = timezone.now()
        return super(UserDataSerializerMixin, self).update(instance, validated_data)
