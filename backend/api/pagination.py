from rest_framework.pagination import PageNumberPagination

from .constants import PAGINATION_PAGE_SIZE


class CustomPagination(PageNumberPagination):
    """Кастомный класс пагинации."""
    page_size = PAGINATION_PAGE_SIZE
    page_size_query_param = 'limit'
