import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers

from recipes.models import (
    Recipe, Tag, Ingredient, RecipeIngredient, Favorite, ShoppingCart
)
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Класс для преобразования строки в изображение"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        file = super().to_internal_value(data)
        if not file.content_type.startswith('image/'):
            raise serializers.ValidationError('Файл должен быть изображением.')
        return file


class CustomUserSerializer(UserSerializer):
    """Сериализатор Users."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            author=obj.id, user=request.user.id
        ).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериазизатор для регистрации Users."""

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def validate_email(self, value):
        """Проверка уникальности email."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value

    def validate_username(self, value):
        """Проверка уникальности username."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким username уже существует."
            )
        return value


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для информации о рецепте для SubscriptionSerializer."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок с учётом ограничения рецептов."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='author.recipes.count',
        read_only=True
    )

    class Meta:
        model = Subscription
        fields = ('author', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Получение рецептов автора."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        # Проверка наличия, является ли числом и больше 0
        if (recipes_limit and recipes_limit.isdigit()
                and int(recipes_limit) > 0):
            recipes = obj.author.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.author.recipes.all()

        return RecipeShortSerializer(recipes, many=True).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
