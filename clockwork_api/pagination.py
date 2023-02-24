from rest_framework.pagination import PageNumberPagination


class DropDownResultSetPagination(PageNumberPagination):
    page_size = 20
