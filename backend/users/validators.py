from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


def validate_username(username):
    """Валидация имени пользователя"""
    if not RegexValidator(r'^[\w.@+-]+\z')(username):
        raise ValidationError(
            'Имя пользователя может содержать только буквы, \
                цифры и символы @/./+/-/_.'
        )