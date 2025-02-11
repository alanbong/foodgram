from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
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

    def create(self, validated_data):
        """Приводит email к нижнему регистру перед созданием пользователя."""
        validated_data['email'] = validated_data['email'].lower()
        return super().create(validated_data)

    def validate(self, attrs):
        """Валидация полей пользователя."""
        if 'email' in attrs:
            attrs['email'] = attrs['email'].lower()

        if (
            self.context.get('request').method == 'PUT'
            and not attrs.get('avatar')
        ):
            raise serializers.ValidationError(
                'Аватар обязателен!'
            )
        return attrs

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного автора."""
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and Subscription.objects.filter(
                author=obj, user=request.user).exists()
        )


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор для отображения подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta:
        model = User
        fields = CustomUserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        """Всегда True, так как это список подписок."""
        return True

    def get_recipes(self, obj):
        """Получение рецептов автора."""
        request = self.context.get('request')

        recipes_limit = request.query_params.get('recipes_limit')

        # Проверка наличия и корректности параметра
        if recipes_limit and recipes_limit.isdigit():
            recipes_limit = int(recipes_limit)
            if recipes_limit > 0:
                recipes = obj.recipes.all()[:recipes_limit]
        else:
            recipes = obj.recipes.all()

        return RecipeShortSerializer(recipes, many=True).data


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для содания подписки."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        """Проверка наличия подписки и на самоподписку."""
        user = self.context['request'].user
        author = data['author']

        if user == author:
            raise serializers.ValidationError(
                {'error': 'Нельзя подписаться на самого себя.'}
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {'error': 'Вы уже подписаны на этого пользователя.'}
            )

        return data

    def to_representation(self, instance):
        """Возвращает подписку через SubscriptionSerializer."""
        return SubscriptionSerializer(
            instance.author, context=self.context
        ).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для информации о рецепте для SubscriptionSerializer."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


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
            return obj.favorite.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Добавлен ли рецепт в список покупок."""
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.shoppingcart.filter(user=user).exists()
        return False


class IngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в RecipeCreateSerializer."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецептов."""
    ingredients = IngredientCreateSerializer(required=True, many=True)
    tags = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField(required=True)

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
        """Валидация полей рецепта."""
        ingredients = attrs.get('ingredients', [])
        tags = attrs.get('tags', [])
        if self.instance is None and 'image' not in attrs:
            raise serializers.ValidationError(
                'Добавьте изображение рецепта!'
            )

        if not tags:
            raise serializers.ValidationError(
                'Добавьте хотя бы один тег!'
            )
        if not ingredients:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент!'
            )

        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError('Теги не должны повторяться.')

        ingredients = [item['ingredient'] for item in ingredients]
        if len(ingredients) != len(set(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )

        return attrs

    @staticmethod
    def handle_ingredients(instance, ingredients_data):
        """Обработка ингредиентов для рецепта."""
        RecipeIngredient.objects.filter(recipe=instance).delete()

        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(recipe=instance, **ingredient_data)
            for ingredient_data in ingredients_data
        ])

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)

        self.handle_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        instance.tags.set(tags_data)
        self.handle_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance, context={'request': self.context.get('request')}
        )

        return serializer.data


class BaseRecipeRelationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для моделей Favorite и ShoppingCart."""

    class Meta:
        fields = ('user', 'recipe')

    def validate(self, data):
        """Проверяет, что рецепт еще не добавлен в список."""
        user = data.get('user')
        recipe = data.get('recipe')
        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {'error': 'Рецепт уже в списке.'}
            )
        data['recipe'] = recipe
        return data

    def to_representation(self, instance):
        """Использует RecipeShortSerializer для представления данных."""
        return RecipeShortSerializer(instance.recipe).data


class FavoriteSerializer(BaseRecipeRelationSerializer):
    """Сериализатор для модели Favorite."""
    class Meta(BaseRecipeRelationSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(BaseRecipeRelationSerializer):
    """Сериализатор для модели ShoppingCart."""
    class Meta(BaseRecipeRelationSerializer.Meta):
        model = ShoppingCart
