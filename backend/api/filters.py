from django.contrib.auth import get_user_model
from django.db import connection
from django_filters import rest_framework as filters
from django.db.models import Q, Value, Case, When, IntegerField
from rest_framework.exceptions import ValidationError

from recipes.models import Recipe, Tag, Ingredient

User = get_user_model()


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if value not in [0, 1]:
            raise ValidationError(
                'Параметр "is_favorited" должен быть 0 или 1.'
            )
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value not in [0, 1]:
            raise ValidationError(
                'Параметр "is_in_shopping_cart" должен быть 0 или 1.'
            )
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_carts__user=self.request.user)
        return queryset


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        method='filter_name', label="Поиск по названию")

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_name(self, queryset, name, value):
        if not value:
            return queryset

        value_lower = value.lower()

        # 🔍 Если база данных - SQLite, фильтруем вручную
        if connection.vendor == 'sqlite':
            # Разделяем на две группы
            starts_with = sorted(
                [obj for obj in queryset
                 if obj.name.lower().startswith(value_lower)],
                key=lambda obj: obj.name
            )
            contains = sorted(
                [obj for obj in queryset if value_lower
                 in obj.name.lower() and obj not in starts_with],
                key=lambda obj: obj.name
            )

            sorted_objects = starts_with + contains
            preserved_order = Case(
                *[When(id=obj.id, then=Value(idx)) for idx, obj
                  in enumerate(sorted_objects)],
                output_field=IntegerField(),
            )

            return queryset.filter(
                id__in=[obj.id for obj in sorted_objects]
            ).order_by(preserved_order)

        # В PostgreSQL работаем стандартным способом
        return queryset.annotate(
            priority=Case(
                When(name__istartswith=value_lower, then=Value(0)),
                When(name__icontains=value_lower, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            )
        ).filter(Q(name__icontains=value_lower)).order_by('priority', 'name')
