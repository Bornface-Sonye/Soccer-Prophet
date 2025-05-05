import re
from django.core.exceptions import ValidationError

def validate_kenyan_phone_number(value):
    value_str = str(value)
    if not re.match(r'^(?:\+254|0)?7\d{8}$', value_str):
        raise ValidationError(
            f'{value} is not a valid Kenyan phone number. It must be in the format 0798073204 or +254798073404.'
        )