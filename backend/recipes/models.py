from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from .constants import (COOKING_TIME_MAX, COOKING_TIME_MIN,
                        INGREDIENT_AMOUNT_MAX, INGREDIENT_AMOUNT_MIN,
                        INGREDIENT_NAME_MAX_LENGTH, INGREDIENT_UNIT_MAX_LENGTH,
                        RECIPE_NAME_MAX_LENGTH, SHORT_LINK_MAX_LENGTH,
                        STR_REPR_MAX_LENGTH, TAG_FIELDS_MAX_LENGTH)

User = get_user_model()


class Recipe(models.Model):
    """Модель рецептов."""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/images',
        verbose_name='Картинка рецепта',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиент'
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes',
        verbose_name='Тег'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                COOKING_TIME_MIN,
                message=f'Минимальное время готовки - {COOKING_TIME_MIN} мин.'
            ),
            MaxValueValidator(
                COOKING_TIME_MAX,
                message=f'Максимальное время готовки - {COOKING_TIME_MAX} мин.'
            ),
        ],
        verbose_name='Время приготовления в минутах'
    )

    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    short_link = models.CharField(
        max_length=SHORT_LINK_MAX_LENGTH,
        verbose_name="Короткая ссылка",
        unique=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.short_link = self.generate_unique_short_url()
        super().save(*args, **kwargs)

    def generate_unique_short_url(self):
        while True:
            short_link = str(uuid4())[:SHORT_LINK_MAX_LENGTH]
            if not Recipe.objects.filter(short_link=short_link).exists():
                return short_link

    def get_absolute_url(self):
        return reverse('recipes-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return (
            f'{self.name[:STR_REPR_MAX_LENGTH]} '
            f'(Автор: {self.author.username[:STR_REPR_MAX_LENGTH]})'
        )


class Tag(models.Model):
    """Модель тегов."""
    name = models.CharField(
        max_length=TAG_FIELDS_MAX_LENGTH,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        max_length=TAG_FIELDS_MAX_LENGTH,
        unique=True,
        verbose_name='Идентификатор'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:STR_REPR_MAX_LENGTH]


class Ingredient(models.Model):
    """Модель рецептов."""
    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_UNIT_MAX_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('name', 'measurement_unit')
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient_name_unit'
            )
        ]

    def __str__(self):
        return self.name[:STR_REPR_MAX_LENGTH]


class RecipeIngredient(models.Model):
    """Промежуточная модель Recipe и Ingredient."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингридиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Название рецепта'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                INGREDIENT_AMOUNT_MIN,
                message=(
                    'Минимальное количество ингредиентов — '
                    f'{INGREDIENT_AMOUNT_MIN}.'
                )
            ),
            MaxValueValidator(
                INGREDIENT_AMOUNT_MAX,
                message=(
                    'Максимальное количество ингредиентов — '
                    f'{INGREDIENT_AMOUNT_MAX}.'
                )
            ),
        ],
        verbose_name='Количество ингредиентов'
    )

    class Meta:
        ordering = ('recipe', 'ingredient')
        verbose_name = 'Ингридиент в рецепте'
        verbose_name_plural = 'Ингридиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient[:STR_REPR_MAX_LENGTH]} {self.amount}шт. '
            f'в {self.recipe[:STR_REPR_MAX_LENGTH]}'
        )


class BaseUserRecipeRelation(models.Model):
    """Базовая модель для избранных рецептов и списка покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        ordering = ('user', 'recipe')
        default_related_name = '%(class)s'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_%(class)s_user_recipe'
            )
        ]

    def __str__(self):
        return (
            f'{self.user.username[:STR_REPR_MAX_LENGTH]} добавил '
            f'{self.recipe.name[:STR_REPR_MAX_LENGTH]}'
        )


class Favorite(BaseUserRecipeRelation):
    """Модель избранных рецептов."""

    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(BaseUserRecipeRelation):
    """Модель списка покупок."""

    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
