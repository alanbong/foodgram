from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator

User = get_user_model()


class Recipe(models.Model):
    """Модель рецептов"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        help_text='Автор рецепта'
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название рецепта',
        help_text='Название рецепта'
    )
    image = models.ImageField(
        verbose_name='Картинка рецепта',
        upload_to='media/'
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        verbose_name='Ингредиент'
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Тег'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(1), 'Минимальное время готовки'],
        help_text='Время приготовления рецепта в минутах'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        oridering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_name_author'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тегов"""
    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        verbose_name='Идентификатор',
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_-]+$',
                message='Slug может содержать только \
                    буквы, цифры, дефисы и подчёркивания.',
                code='invalid_slug'
            )
        ]
    )

    class Meta:
        ordering = ['id']
        verbose_name = "Тег"
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель рецептов."""
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=128,
        unique=True,
        help_text='Введите название ингредиента')
    measurement_unit = models.CharField(
        max_length=64,        
        verbose_name='Единица измерения',
        help_text='Единица измерения')

    class Meta:
        ordering = ['id']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}'


class RecipeIngredient(models.Model):
    pass