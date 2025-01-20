from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from .constants import MAX_LENGTH_150, USER_ROLE, ADMIN_ROLE
from .validators import validate_username

ROLE_CHOICES = [
    (USER_ROLE, 'User'),
    (ADMIN_ROLE, 'Admin'),
]


class UserModel(AbstractUser):
    """Кастомная модель пользователя с поддержкой ролей."""
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Адрес электронной почты'
    )
    username = models.CharField(
        max_length=MAX_LENGTH_150,
        unique=True,
        validators=[
            validate_username
        ],
        verbose_name='Username'
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_150,
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_150,
        verbose_name="Фамилия"
    )
    role = models.CharField(
        max_length=max(len(role[0]) for role in ROLE_CHOICES),
        choices=ROLE_CHOICES,
        default=USER_ROLE,
        verbose_name='Роль'
    )
    avatar = models.ImageField(
        upload_to='media/avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар профиля'
    )

    @property
    def is_admin(self):
        return self.role == ADMIN_ROLE or self.is_superuser or self.is_staff

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username[:50]
