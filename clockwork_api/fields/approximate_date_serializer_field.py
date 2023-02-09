from django_date_extensions.fields import ApproximateDate
from rest_framework import serializers


class ApproximateDateSerializerField(serializers.Field):
    """
    Date objects are serialized to an ApproximateDate object.
    """
    def to_representation(self, value):
        return str(value)

    def to_internal_value(self, data):
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
            msg = 'Invalid date: %s' % str(e)
            raise serializers.ValidationError(msg)

