from django.urls import path

from rest_framework.routers import DefaultRouter

from . import views

app_name = "polls"


router = DefaultRouter()
router.register(
    r'questions', 
    views.QuestionViewSet, 
    basename='question-api'
)

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    path("<int:question_id>/vote/", views.vote, name="vote"),
    path('add/', views.AddQuestionView.as_view(), name='add_question'),

   path('test-n1/', views.test_n1_query, name='test_n1_query'),
]   