from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static
from foodgram_backend.settings import BASE_DIR

DOCS_DIR = BASE_DIR.parent / 'docs'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        'redoc/',
        serve,
        {'path': 'redoc.html', 'document_root': DOCS_DIR},
        name='redoc'
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
