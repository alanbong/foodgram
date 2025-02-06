from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
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
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value not in [0, 1]:
            raise ValidationError(
                'Параметр "is_in_shopping_cart" должен быть 0 или 1.'
            )
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_name(self, queryset, name, value):
        starts_with = queryset.filter(name__istartswith=value)
        contains = queryset.filter(
            name__icontains=value
        ).exclude(id__in=starts_with.values('id'))
        return starts_with.union(contains)
