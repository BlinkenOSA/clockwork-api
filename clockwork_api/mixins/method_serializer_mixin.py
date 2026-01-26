from rest_framework import exceptions


class MethodSerializerMixin:
    """
    Dynamic serializer selection mixin based on HTTP request method.

    This mixin enables Django REST Framework views to use different
    serializers depending on the incoming HTTP method (GET, POST, PUT, etc.).

    It is primarily used in views that combine multiple operations
    (e.g. list + create, retrieve + update + delete) and require
    different serializers for read and write operations.

    This avoids splitting endpoints into multiple views while still
    preserving proper separation between:

        - Read serializers (optimized for output)
        - Write serializers (optimized for validation and input)

    Usage:

        class ExampleView(MethodSerializerMixin, generics.ListCreateAPIView):

            method_serializer_classes = {
                ('GET', ): ExampleReadSerializer,
                ('POST', ): ExampleWriteSerializer,
                ('PUT', 'PATCH'): ExampleWriteSerializer,
            }

    How It Works:

        - The mixin inspects the current HTTP request method.
        - It looks up the corresponding serializer in
          `method_serializer_classes`.
        - The first matching entry is returned.
        - If no match is found, a MethodNotAllowed exception is raised.

    Benefits:

        - Keeps REST endpoints compact
        - Improves API consistency
        - Prevents accidental use of write serializers for reads
        - Reduces duplicated view code
        - Encourages clean separation of concerns
    """

    #: Mapping of HTTP methods to serializer classes.
    #: Must be defined in subclasses.
    #:
    #: Example:
    #: {
    #:     ('GET', ): ReadSerializer,
    #:     ('POST', ): WriteSerializer,
    #: }
    method_serializer_classes = None

    def get_serializer_class(self):
        """
        Return the appropriate serializer class for the current request method.

        The method iterates through the `method_serializer_classes` mapping
        and selects the first serializer whose HTTP method tuple contains
        the current request method.

        Raises:
            AssertionError:
                If `method_serializer_classes` is not defined on the view.

            MethodNotAllowed:
                If the current HTTP method is not mapped to any serializer.

        Returns:
            rest_framework.serializers.Serializer:
                The serializer class associated with the request method.
        """
        assert self.method_serializer_classes is not None, (
            'Expected view %s should contain method_serializer_classes '
            'to get right serializer class.' %
            (self.__class__.__name__, )
        )

        for methods, serializer_cls in self.method_serializer_classes.items():
            if self.request._request.method in methods:
                return serializer_cls

        raise exceptions.MethodNotAllowed(self.request.method)
