from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)
from users.models import Subscription

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    CustomUserSerializer, FavoriteSerializer, IngredientSerializer,
    RecipeCreateSerializer, RecipeSerializer, ShoppingCartSerializer,
    SubscriptionCreateSerializer, SubscriptionSerializer, TagSerializer
)


User = get_user_model()


class UsersViewSet(UserViewSet):
    """Кастомный ViewSet для пользователей."""
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()

    @action(
        detail=False,
        methods=('get',),
        permission_classes=[IsAuthenticated]
    )
    def me(self, request, *args, **kwargs):
        """Ограниченный доступ к профилю текущего пользователя."""
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=('put',),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def add_avatar(self, request):
        """Добавление аватара пользователю."""
        serializer = self.get_serializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'avatar': serializer.data['avatar']}, status=status.HTTP_200_OK
        )

    @add_avatar.mapping.delete
    def remove_avatar(self, request):
        """Удаление аватара пользователя."""
        user = request.user
        if not user.avatar:
            return Response(
                {'detail': 'Аватар отсутствует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.avatar.delete(save=True)
        return Response(
            {'detail': 'Аватар успешно удален.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=('post',),
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def add_subscription(self, request, id=None):
        """Подписка на пользователя."""
        author = get_object_or_404(User, pk=id)
        serializer = SubscriptionCreateSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        return Response(
            SubscriptionSerializer(
                subscription, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @add_subscription.mapping.delete
    def remove_subscription(self, request, id=None):
        """Удаление подписки на пользователя."""
        author = get_object_or_404(User, pk=id)
        deleted, _ = Subscription.objects.filter(
            user=request.user, author=author
        ).delete()

        if not deleted:
            return Response(
                {'error': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Получение списка подписок пользователя."""
        user = request.user
        subscriptions = Subscription.objects.filter(
            user=user
        ).prefetch_related('author__recipes')
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def _add_recipe_to_list(self, serializer_class, request, pk):
        """Общий метод для добавления рецепта в список."""
        context = {'request': request, 'recipe_id': pk}
        serializer = serializer_class(data={}, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_recipe_from_list(self, serializer_class, request, pk):
        """Общий метод для удаления рецепта из списка."""
        recipe = get_object_or_404(Recipe, id=pk)

        model = serializer_class.Meta.model

        deleted_count, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'errors': 'Рецепт не найден в списке.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def add_favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        return self._add_recipe_to_list(
            FavoriteSerializer, request, pk
        )

    @add_favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""
        return self._remove_recipe_from_list(
            FavoriteSerializer, request, pk
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def add_to_shopping_cart(self, request, pk=None):
        """Добавление рецепта в список покупок."""
        return self._add_recipe_to_list(
            ShoppingCartSerializer, request, pk
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """Удаление рецепта из списка покупок"""
        return self._remove_recipe_from_list(
            ShoppingCartSerializer, request, pk
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        recipes = shopping_cart.values_list('recipe_id', flat=True)

        # Собираем ингредиенты с их общим количеством
        ingredients = (
            RecipeIngredient.objects.filter(recipe_id__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        purchased = ['Список покупок:']
        for item in ingredients:
            purchased.append(
                f"{item['ingredient__name']}: {item['total_amount']} "
                f"{item['ingredient__measurement_unit']}"
            )

        # Создаем HTTP-ответ
        content = "\n".join(purchased)
        response = HttpResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename=shopping-list.txt'

        return response

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_url = (
            f"{self.request.scheme}://"
            f"{self.request.get_host()}/r/"
            f"{recipe.short_link}"
        )
        return Response({"short-link": short_url}, status=status.HTTP_200_OK)


@require_http_methods(['GET'])
def redirect_short_link(request, short_link):
    """Переадресовывает на оригинальный рецепт."""
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(f'/recipes/{recipe.id}')
