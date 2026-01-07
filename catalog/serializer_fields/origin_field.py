"""
Custom serializer field for normalizing request item origin values.

This field maps human-readable origin labels received from the client
into internal origin codes used by the system.

The mapping enforces a strict whitelist to prevent invalid or unexpected
origin values from entering the request processing pipeline.
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class OriginField(serializers.CharField):
    """
    Normalizes user-facing origin labels into internal origin codes.

    Accepted input values:
        - "Archives"      → "FA"
        - "Library"       → "L"
        - "Film Library"  → "FL"

    Any other value is rejected.

    This field ensures downstream logic can safely branch on
    a known set of origin codes.
    """

    def to_internal_value(self, value: str) -> str:
        """
        Converts a human-readable origin label to an internal code.

        Args:
            value:
                Origin label provided by the client.

        Returns:
            Internal origin code string.

        Raises:
            ValidationError if the origin label is not recognized.
        """
        origin_values = {
            'Archives': 'FA',
            'Library': 'L',
            'Film Library': 'FL'
        }
        if value not in origin_values:
            raise ValidationError('Invalid value!')

        return origin_values[value]
