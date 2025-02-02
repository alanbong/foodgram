from rest_framework.permissions import IsAuthenticatedOrReadOnly, SAFE_METHODS


class IsSelfOrAdminOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение для работы с профилями пользователей.
    - Доступ для чтения всем
    - Доступ для редактирования администратору и владельцу профиля.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_admin
            or obj.id == request.user
        )

class IsOwnerOrAdminOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение для работы с рецептами.
    - Доступ для чтения всем
    - Доступ для редактирования администратору и автору.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_admin
            or obj.author == request.user
        )
