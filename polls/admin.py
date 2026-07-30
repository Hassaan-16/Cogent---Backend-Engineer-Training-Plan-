from django.contrib import admin

from .forms import QuestionForm
from .models import Choice, Question


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    form = QuestionForm
    list_display = ["question_text", "pub_date", "was_published_recently"]
    actions = ["publish_now"]
    fieldsets = [
        (None, {"fields": ["question_text"]}),
        ("Date information", {"fields": ["pub_date"], "classes": ["collapse"]}),
    ]
    inlines = [ChoiceInline]
    search_fields = ["question_text"]
    list_filter = ["pub_date"]


admin.site.register(Question, QuestionAdmin)
