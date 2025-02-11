from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .constants import STR_REPR_MAX_LENGTH, USER_PERSONAL_FIELDS_MAX_LENGTH


class UserModel(AbstractUser):
    """Кастомная модель пользователя с поддержкой ролей."""
    email = models.EmailField(
        unique=True,
        verbose_name='Адрес электронной почты'
    )
    username = models.CharField(
        max_length=USER_PERSONAL_FIELDS_MAX_LENGTH,
        unique=True,
        validators=[
            UnicodeUsernameValidator()
        ],
        verbose_name='Username'
    )
    first_name = models.CharField(
        max_length=USER_PERSONAL_FIELDS_MAX_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=USER_PERSONAL_FIELDS_MAX_LENGTH,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='users/image',
        blank=True,
        null=True,
        verbose_name='Аватар профиля'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    @property
    def is_admin(self):
        return self.is_superuser

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username[:STR_REPR_MAX_LENGTH]


User = get_user_model()


class Subscription(models.Model):
    """Модель подписок пользователей на авторов рецептов."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name="Автор"
    )

    class Meta:
        ordering = ('user', 'author')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            ),

            models.CheckConstraint(
                check=models.Q(
                    _negated=True,
                    user=models.F('author')
                ),
                name='user_cant_follow_himself'
            )
        ]

    def __str__(self):
        return (
            f'{self.user.username[:STR_REPR_MAX_LENGTH ]} '
            f'подписан {self.author.username[:STR_REPR_MAX_LENGTH]}'
        )
