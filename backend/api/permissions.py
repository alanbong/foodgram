from rest_framework.permissions import (
    SAFE_METHODS, IsAuthenticatedOrReadOnly
)


class IsOwnerOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение для работы с рецептами.
    - Доступ для чтения всем
    - Доступ для редактирования, удалению автору.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )
