from django.urls import path, include
from django.views.static import serve
from rest_framework.routers import DefaultRouter

from foodgram_backend.settings import BASE_DIR
from .views import (
    UsersViewSet, TagViewSet, IngredientViewSet
)

DOCS_DIR = BASE_DIR.parent / 'docs'

router = DefaultRouter()
router.register(r'users', UsersViewSet, basename='users')
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
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
