from django.core import validators
from django.db import models


class EmailNullField(models.CharField):
    """
    Subclass of the CharField that allows empty strings to be stored as NULL.
    This class is used to set charfield be optional but unique when added.
    Set blank=True, null=True when declaring the field
    """
    description = "EmailField that stores NULL but returns ''."
    default_validators = [validators.validate_email]

    def get_prep_value(self, value):
        """
        Catches value right before sending to db.
        """
        if value == '':  # If Django tries to save an empty string, send the db None (NULL).
            return None
        else:  # Otherwise, just pass the value.
            return value

    def from_db_value(self, value, expression, connection):
        """
        Gets value right out of the db and changes it if its ``None``.
        """
        if value is None:
            return ''
        else:
            return value

    def to_python(self, value):
        """
        Gets value right out of the db or an instance, and changes it if its ``None``.
        """
        if isinstance(value, models.CharField):  # If an instance, just return the instance.
            return value
        if value is None:  # If db has NULL, convert it to ''.
            return ''
        return value  # Otherwise, just return the value.
