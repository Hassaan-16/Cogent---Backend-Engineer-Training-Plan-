from rest_framework.pagination import CursorPagination

class QuestionCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-pub_date'
    