class ReadWriteSerializerMixin:
    """
    Serializer selection mixin for separating read and write operations in ViewSets.

    This mixin dynamically chooses between a "read" serializer and a "write"
    serializer based on the current ViewSet action.

    It is designed specifically for Django REST Framework ViewSets, where
    the `action` attribute is automatically set (list, retrieve, create, etc.).

    The mixin enforces a clear separation between:

        - Read serializers:
              Used for list/retrieve operations
              Optimized for output formatting and nested representation

        - Write serializers:
              Used for create/update/destroy operations
              Optimized for validation and input handling

    This pattern improves:

        - API consistency
        - Validation safety
        - Performance
        - Code maintainability
        - Documentation clarity

    Usage Example:

        class ExampleViewSet(ReadWriteSerializerMixin, ModelViewSet):

            queryset = Example.objects.all()

            read_serializer_class = ExampleReadSerializer
            write_serializer_class = ExampleWriteSerializer

    Action → Serializer Mapping:

        list            → read_serializer_class
        retrieve        → read_serializer_class
        create          → write_serializer_class
        update          → write_serializer_class
        partial_update  → write_serializer_class
        destroy         → write_serializer_class
    """

    #: Serializer used for read-only operations (list, retrieve).
    read_serializer_class = None

    #: Serializer used for write operations (create, update, delete).
    write_serializer_class = None

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the current action.

        The method inspects the `action` attribute provided by DRF ViewSets
        and maps it to either the read or write serializer.

        Returns:
            rest_framework.serializers.Serializer:
                Selected serializer class.

        Raises:
            AssertionError:
                If the required serializer class is not defined.
        """
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return self.get_write_serializer_class()

        return self.get_read_serializer_class()

    def get_read_serializer_class(self):
        """
        Return the serializer class used for read operations.

        This method ensures that `read_serializer_class` is configured
        before use.

        Returns:
            rest_framework.serializers.Serializer:
                Read serializer class.

        Raises:
            AssertionError:
                If `read_serializer_class` is not set.
        """
        assert self.read_serializer_class is not None, (
            "'%s' should either include a `read_serializer_class` attribute, "
            "or override the `get_read_serializer_class()` method."
            % self.__class__.__name__
        )

        return self.read_serializer_class

    def get_write_serializer_class(self):
        """
        Return the serializer class used for write operations.

        This method ensures that `write_serializer_class` is configured
        before use.

        Returns:
            rest_framework.serializers.Serializer:
                Write serializer class.

        Raises:
            AssertionError:
                If `write_serializer_class` is not set.
        """
        assert self.write_serializer_class is not None, (
            "'%s' should either include a `write_serializer_class` attribute, "
            "or override the `get_write_serializer_class()` method."
            % self.__class__.__name__
        )

        return self.write_serializer_class
