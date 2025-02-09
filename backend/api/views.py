from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.views.decorators.http import require_http_methods
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsOwnerOrAdminOrReadOnly, IsAdmin
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeSerializer,
                          SubscriptionSerializer, TagSerializer,
                          FavoriteSerializer, ShoppingCartSerializer)


User = get_user_model()


class UsersViewSet(UserViewSet):
    """Кастомный ViewSet для пользователей."""
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()

    # в докуентации djoser сказано, что можно добавить
    # 'current_user': ['rest_framework.permissions.IsAuthenticated'],
    # однако, как бы я не пытался, без данного метода не работало корректно
    def get_permissions(self):
        """
        Динамическое назначение разрешений в зависимости от действия.
        """
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def manage_avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'detail': 'Поле avatar обязательно.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(
                user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {'avatar': serializer.data['avatar']},
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        if not user.avatar:
            return Response(
                {'detail': 'Аватар отсутствует.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.avatar.delete(save=True)
        user.save()
        return Response(
            {'detail': 'Аватар успешно удален.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def manage_subscription(self, request, id=None):
        """Подписка и отписка на пользователя."""
        user = request.user
        author = get_object_or_404(User, pk=id)

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'error': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = SubscriptionSerializer(
                subscription, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        subscription = Subscription.objects.filter(
            user=user, author=author).first()
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Вы не подписаны на этого пользователя.'},
            status=status.HTTP_400_BAD_REQUEST
        )

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

    @action(
        detail=True,
        methods=['post'],
        url_path='admin-delete',
        permission_classes=(IsAdmin,)
    )
    def admin_delete_user(self, request, id=None):
        """
        Удаление пользователя администратором.
        """
        # Получаем пользователя, которого хотят удалить
        user = get_object_or_404(User, id=id)

        if user == request.user:
            return Response(
                {'error': 'Администратор не может удалить сам себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_superuser:
            return Response(
                {'error': 'Нельзя удалить суперпользователя.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user.delete()
        return Response(
            {'detail': f'Пользователь {user.username} успешно удален.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=('post', 'put'),
        permission_classes=(IsAuthenticated,),
        url_path='set_password',
    )
    def set_password(self, request, *args, **kwargs):
        """
        Переопределенный метод изменения пароля:
        - Обычные пользователи меняют свой пароль стандартно.
        - Администраторы могут менять пароль любого пользователя
        используя ('user_id' в запросе).
        """
        user = request.user

        if 'user_id' in request.data and not user.is_admin:
            return Response(
                {'error': (
                    'Вы не можете изменить пароль другого пользователя.')},
                status=status.HTTP_403_FORBIDDEN
            )

        # Если администратор передал 'user_id',
        # меняем пароль указанного пользователя
        if user.is_admin and 'user_id' in request.data:
            user_id = request.data['user_id']
            new_password = request.data['new_password']

            target_user = get_object_or_404(User, pk=user_id)
            target_user.set_password(new_password)
            target_user.save()

            return Response(
                {'detail': (
                    f'Пароль пользователя {target_user.username} '
                    'успешно изменен.'
                )},
                status=status.HTTP_200_OK
            )

        # Если обычный пользователь, убираем `user_id` и передаем в Djoser
        data_without_user_id = request.data.copy()
        data_without_user_id.pop('user_id', None)

        return super().set_password(
            request, *args, data=data_without_user_id, **kwargs
        )


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
    permission_classes = (IsOwnerOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def _get_recipe_and_model(self, serializer_class, pk, user):
        """
        Общий метод для получения рецепта, модели и проверки наличия связи.
        """
        # Получаем рецепт
        recipe = get_object_or_404(Recipe, id=pk)

        # Получаем модель из сериализатора
        model = serializer_class.Meta.model

        # Проверяем наличие связи
        relation_exists = model.objects.filter(
            user=user, recipe=recipe
        ).exists()

        return recipe, model, relation_exists

    def _add_recipe_to_list(self, serializer_class, request, pk):
        """Общий метод для добавления рецепта в список."""
        _, _, relation_exists = self._get_recipe_and_model(
            serializer_class, pk, request.user
        )

        # Проверяем, что рецепт еще не добавлен в список
        if relation_exists:
            return Response(
                {'errors': 'Рецепт уже находится в списке.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Проверяем валидность через сериализатор
        context = {'request': request, 'recipe_id': pk}
        serializer = serializer_class(data={}, context=context)
        serializer.is_valid(raise_exception=True)

        # Создаем связь
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_recipe_from_list(self, serializer_class, request, pk):
        """Общий метод для удаления рецепта из списка."""
        recipe, model, relation_exists = self._get_recipe_and_model(
            serializer_class, pk, request.user
        )

        if not relation_exists:
            return Response(
                {'errors': 'Рецепт не найден в списке.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Удаляем связь
        model.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def favorite(self, request, pk=None):
        """Добавление и удаление рецептов из избранного."""
        if request.method == 'POST':
            return self._add_recipe_to_list(
                FavoriteSerializer, request, pk
            )
        if request.method == 'DELETE':
            return self._remove_recipe_from_list(
                FavoriteSerializer, request, pk
            )
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецептов из списка покупок."""
        if request.method == 'POST':
            return self._add_recipe_to_list(
                ShoppingCartSerializer, request, pk
            )
        if request.method == 'DELETE':
            return self._remove_recipe_from_list(
                ShoppingCartSerializer, request, pk
            )
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        # recipes = [item.recipe.id for item in shopping_cart]
        recipes = shopping_cart.values_list('recipe_id', flat=True)
        # ingredients = (
        #     RecipeIngredient.objects.filter(recipe__in=recipes)
        #     .values('ingredient')
        #     .annotate(total_amount=Sum('amount'))
        # )

        # Собираем ингредиенты с их общим количеством
        ingredients = (
            RecipeIngredient.objects.filter(recipe_id__in=recipes)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        purchased = ['Список покупок:']
        for item in ingredients:
            # ingredient = Ingredient.objects.get(pk=item['ingredient'])
            # total_amount = item['total_amount']
            # purchased.append(
            #     f'{ingredient.name}: {total_amount}, '
            #     f'{ingredient.measurement_unit}'
            # )
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
        if not recipe.short_link:
            recipe.short_link = recipe.generate_unique_short_url()
            recipe.save()
        short_url = (
            f"{self.request.scheme}://"
            f"{self.request.get_host()}/r/"
            f"{recipe.short_link}"
        )
        return Response({"short-link": short_url}, status=status.HTTP_200_OK)


@require_http_methods(["GET"])
def redirect_short_link(request, short_link):
    """Переадресовывает на оригинальный рецепт."""
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(f"/recipes/{recipe.id}")
