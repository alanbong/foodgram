from rest_framework.permissions import (
    BasePermission, SAFE_METHODS, IsAuthenticatedOrReadOnly
)


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
            or request.user.is_staff
            or obj.id == request.user
        )


class IsOwnerOrAdminOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение для работы с рецептами.
    - Доступ для чтения всем
    - Доступ для редактирования, удалению администратору и автору.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_admin
            or request.user.is_staff
            or obj.author == request.user
        )


class IsAdmin(BasePermission):
    """
    Проверка, является ли пользователь администратором.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.is_admin
                or request.user.is_staff
            )
        )
