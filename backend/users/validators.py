from django.core.exceptions import ValidationError


def validate_lowercase_email(value):
    """Проверяет, что email в нижнем регистре."""
    if value != value.lower():
        raise ValidationError('Email должен быть в нижнем регистре.')
