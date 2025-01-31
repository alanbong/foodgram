from rest_framework.permissions import IsAuthenticatedOrReadOnly, SAFE_METHODS


class IsOwnerOrAdminOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Доступ для чтения всем, а для редактирования автору,
    модератору или администратору.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return (
            request.user.is_admin
            or obj.id == request.user
            or obj.author == request.user
        )
