from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_username(username):
    """Валидация имени пользователя"""
    validator = RegexValidator(
        r'^[\w.@+-]+$',
        message=(
            "Имя пользователя может содержать только буквы, "
            "цифры и символы @/./+/-/_."
        )
    )
    validator(username)
