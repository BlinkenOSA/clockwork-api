from django.db import models


class DetectProtectedMixin:
    """
    Mixin for detecting whether a model instance can be safely deleted.

    This mixin inspects all reverse relationships of a model instance and
    determines whether any related objects would block deletion due to
    PROTECT constraints.

    It is primarily used to support UI logic (e.g., disabling delete buttons)
    and API validation by exposing a simple `is_removable()` check.

    Behavior:
        - Iterates over all related models defined in Django's relation tree
        - Examines each relation's `on_delete` policy
        - Identifies relations using `models.PROTECT`
        - Checks if protected related objects exist

    If any protected related object exists, the instance is considered
    non-removable.

    Supported on_delete behaviors:
        - PROTECT    → Prevents deletion if related objects exist
        - CASCADE    → Ignored (safe to delete)
        - SET_NULL   → Ignored
        - DO_NOTHING → Ignored
        - None       → Ignored

    Intended use:
        Mixed into Django models that require controlled deletion behavior.

    Example:
        class Researcher(models.Model, DetectProtectedMixin):
            ...

        if researcher.is_removable():
            researcher.delete()
    """

    def is_removable(self) -> bool:
        """
        Determine whether the instance can be safely deleted.

        Scans reverse relationships and checks for related objects that use
        `on_delete=models.PROTECT`.

        Returns:
            bool:
                True  → No protected related objects exist (safe to delete)
                False → One or more protected relations exist (deletion blocked)
        """
        state = True

        # Iterate over all reverse relationships
        for relation in self._meta._relation_tree:

            on_delete = relation.remote_field.on_delete

            # Skip relations without deletion constraints
            if on_delete in [None, models.DO_NOTHING]:
                continue

            # Build reverse filter (e.g. related_model.objects.filter(fk=self))
            filter_kwargs = {relation.name: self}

            related_queryset = relation.model.objects.filter(**filter_kwargs)

            # Block deletion if protected relations exist
            if on_delete == models.PROTECT:
                if related_queryset.exists():
                    state = False

        return state
