from django.urls import include, path
from django.views.static import serve
from rest_framework.routers import DefaultRouter

from foodgram_backend.settings import BASE_DIR

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet, UsersViewSet,
                    redirect_short_link)

DOCS_DIR = BASE_DIR.parent / 'docs'

router = DefaultRouter()
router.register('users', UsersViewSet, basename='users')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    # Маршрут для переадресации по короткой ссылке
    path('r/<str:short_link>/', redirect_short_link,
         name='redirect-short-link'),
    path('', include(router.urls)),
    path(
        'redoc/', serve,
        {'path': 'redoc.html', 'document_root': DOCS_DIR},
        name='redoc'
    ),
    path(
        'redoc/openapi-schema.yml', serve,
        {'path': 'openapi-schema.yml', 'document_root': DOCS_DIR},
        name='redoc'
    ),
]
