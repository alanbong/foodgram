import os

from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'docs')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        'redoc/',
        serve,
        {'path': 'redoc.html', 'document_root': DOCS_DIR},
        name='redoc'
    ),
    path(
        'redoc/openapi-schema.yml',
        serve,
        {'path': 'openapi-schema.yml', 'document_root': DOCS_DIR},
        name='openapi-schema'
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
