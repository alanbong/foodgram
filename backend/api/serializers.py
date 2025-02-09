import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
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
        request = self.context.get('request')
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
                'Пользователь с таким email уже существует.'
            )
        return value

    def validate_username(self, value):
        """Проверка уникальности username."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким username уже существует.'
            )
        return value


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для информации о рецепте для SubscriptionSerializer."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок с учётом ограничения рецептов."""
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='author.recipes.count',
        read_only=True
    )

    class Meta:
        model = Subscription
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count',
        )

    def get_is_subscribed(self, obj):
        """Проверка подписки текущего пользователя на автора."""
        user = self.context.get('request').user
        return Subscription.objects.filter(
            user=user, author=obj.author
        ).exists()

    def get_avatar(self, obj):
        """Возвращает полный URL для аватара."""
        if obj.author and obj.author.avatar:
            return obj.author.profile.avatar.url
        return None

    def get_recipes(self, obj):
        """Получение рецептов автора."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        # Проверка наличия и корректности параметра
        if recipes_limit:
            if not recipes_limit.isdigit():
                raise serializers.ValidationError({
                    'recipes_limit': (
                        'Параметр должен быть положительным '
                        'целым числом.'
                    )
                })
            recipes_limit = int(recipes_limit)
            if recipes_limit <= 0:
                raise serializers.ValidationError({
                    'recipes_limit': (
                        'Параметр должен быть больше нуля.'
                    )
                })
            recipes = obj.author.recipes.all()[:recipes_limit]
        else:
            recipes = obj.author.recipes.all()

        return RecipeShortSerializer(recipes, many=True).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в RecipeSerializer."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = ('id', 'author')

    def get_is_favorited(self, obj):
        """Добавлен ли рецепт в избранное."""
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Добавлен ли рецепт в список покупок."""
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.in_shopping_carts.filter(user=user).exists()
        return False


class IngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в RecipeCreateSerializer."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецептов."""
    ingredients = IngredientCreateSerializer(required=True, many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate(self, attrs):
        required_fields = [
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        ]
        missing_fields = [
            field for field in required_fields if field not in attrs
        ]

        if missing_fields:
            raise serializers.ValidationError({
                field: 'Это поле обязательно.' for field in missing_fields
            })

        return attrs

    def validate_tags(self, value):
        """Проверка уникальности тегов."""
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один тег!'
            )
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    def validate_ingredients(self, value):
        """Проверка уникальности ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент!'
            )
        ingredients = [item['ingredient'] for item in value]
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )

        return value

    def handle_ingredients(self, instance, ingredients_data):
        """Обработка ингредиентов для рецепта."""
        RecipeIngredient.objects.filter(recipe=instance).delete()
        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['ingredient']
            amount = ingredient_data['amount']
            RecipeIngredient.objects.update_or_create(
                recipe=instance,
                ingredient=ingredient,
                defaults={'amount': amount}
            )

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe, created = Recipe.objects.get_or_create(
            author=author,
            name=validated_data['name'],
            defaults=validated_data
        )
        if not created:
            raise serializers.ValidationError({
                'name': 'У вас уже существует рецепт с таким названием.'
            })
        recipe.tags.set(tags_data)

        self.handle_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.ingredients.clear()
            self.handle_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance, context={'request': self.context.get('request')}
        )

        return serializer.data


class BaseRecipeRelationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для моделей Favorite и ShoppingCart."""
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.SerializerMethodField()
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        """Возвращает полный URL изображения рецепта."""
        return obj.recipe.image.url if obj.recipe.image else None

    def create(self, validated_data):
        """Создает объект ShoppingCart/Favorite."""
        user = self.context['request'].user
        recipe_id = self.context.get('recipe_id')
        recipe = Recipe.objects.get(id=recipe_id)
        return self.Meta.model.objects.create(user=user, recipe=recipe)


class FavoriteSerializer(BaseRecipeRelationSerializer):
    """Сериализатор для модели Favorite."""
    class Meta(BaseRecipeRelationSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(BaseRecipeRelationSerializer):
    """Сериализатор для модели ShoppingCart."""
    class Meta(BaseRecipeRelationSerializer.Meta):
        model = ShoppingCart


class SetPasswordByAdminSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля администратором."""
    user_id = serializers.IntegerField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_user_id(self, value):
        """Проверка, что пользователь с таким ID существует."""
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Пользователь не найден.")
        return value
