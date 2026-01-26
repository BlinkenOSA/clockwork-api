from django_date_extensions.fields import ApproximateDate
from rest_framework import serializers


class ApproximateDateSerializerField(serializers.Field):
    """
    Serializer field for handling approximate or partial dates.

    This custom DRF field converts string-based date representations
    into ApproximateDate objects and vice versa.

    Supported input formats:
        - "YYYY"           → Year only
        - "YYYY-MM"        → Year and month
        - "YYYY-MM-DD"     → Full date
        - "" (empty)       → Interpreted as null

    Missing date components are automatically set to zero.

    Example mappings:
        "1989"        → ApproximateDate(1989, 0, 0)
        "1989-06"     → ApproximateDate(1989, 6, 0)
        "1989-06-12"  → ApproximateDate(1989, 6, 12)

    Intended use:
        - Archival metadata with uncertain or incomplete dates
        - Historical records
        - Finding aids and catalog descriptions

    Validation:
        Raises ValidationError for invalid date values.
    """

    def to_representation(self, value):
        """
        Converts an ApproximateDate object to its string representation.

        Args:
            value (ApproximateDate): Stored date value.

        Returns:
            str: ISO-like date string (YYYY, YYYY-MM, or YYYY-MM-DD).
        """
        return str(value)

    def to_internal_value(self, data):
        """
        Parses a string into an ApproximateDate instance.

        Accepts partial date formats and converts missing components
        to zero.

        Args:
            data (str): Date string in supported format.

        Returns:
            ApproximateDate | None: Parsed date object or None if empty.

        Raises:
            serializers.ValidationError:
                If the date format or values are invalid.
        """
        year, month, day = [0, 0, 0]

        if data == "":
            return None

        dates = data.split('-')

        if len(dates) == 1:
            year = dates[0]
            month = 0
            day = 0

        elif len(dates) == 2:
            year, month = dates
            day = 0

        elif len(dates) == 3:
            year, month, day = dates

        try:
            return ApproximateDate(int(year), int(month), int(day))

        except ValueError as e:
            msg = f'Invalid date: {str(e)}'
            raise serializers.ValidationError(msg)
