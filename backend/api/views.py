from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination


from recipes.models import (
    Ingredient,
    Favorite,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)

from .serializers import CustomUserSerializer
from .permissions import IsOwnerOrAdminOrReadOnly


User = get_user_model()


class CustomPagination(PageNumberPagination):
    """Кастомный класс пагинации."""
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100


class UsersViewSet(UserViewSet):
    """Кастомный ViewSet для пользователей."""
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    pagination_class = CustomPagination
