from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.cache import cache_page
from django.views.generic.edit import CreateView
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .forms import QuestionForm
from .models import Choice, Question
from .pagination import QuestionCursorPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import QuestionSerializer, VoteSerializer
from .services import send_vote_analytics


def test_n1_query(request):
    choices = Choice.objects.select_related("question").all()
    output = []
    for choice in choices:
        output.append(choice.question.question_text)

    return HttpResponse("<br>".join(output))


@method_decorator(cache_page(60 * 15), name="list")
class QuestionViewSet(viewsets.ModelViewSet):
    """
    This ViewSet automatically provides 'list', 'create', 'retrieve',
    'update', and 'destroy' actions.
    """

    queryset = (
        Question.objects.select_related("author").prefetch_related("choice_set").all()
    )

    serializer_class = QuestionSerializer
    pagination_class = QuestionCursorPagination
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = ["author"]
    search_fields = ["question_text"]
    ordering_fields = ["pub_date", "author"]
    ordering = ["-pub_date"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == "vote":
            return [IsAuthenticated()]

        return super().get_permissions()

    @action(detail=True, methods=["post"], serializer_class=VoteSerializer)
    def vote(self, request, pk=None, **kwargs):
        question = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        choice_id = serializer.validated_data["choice_id"]

        try:
            selected_choice = question.choice_set.get(pk=choice_id)

            selected_choice.votes = F("votes") + 1
            selected_choice.save()

            # --- NEW: Trigger external service ---
            send_vote_analytics(selected_choice.id)
            # -------------------------------------

            return Response(
                {"message": "Vote recorded successfully!"}, status=status.HTTP_200_OK
            )

        except Choice.DoesNotExist:
            return Response(
                {
                    "error_code": "INVALID_CHOICE",
                    "message": "This choice does not exist for this question.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class AddQuestionView(CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "polls/add_question.html"
    success_url = reverse_lazy("polls:index")


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """

        # time.sleep(2) # check for custom middleware implementation

        return (
            Question.objects.filter(pub_date__lte=timezone.now())
            .prefetch_related("choice_set")
            .order_by("-pub_date")[:5]
        )


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).prefetch_related(
            "choice_set"
        )


class ResultsView(LoginRequiredMixin, generic.DetailView):
    model = Question
    template = "polls/results.html"


@action(detail=True, methods=["post"], serializer_class=VoteSerializer)
def vote(request, question_id, **kwargs):
    question = get_object_or_404(Question, pk=question_id)

    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])

    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )

    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()

        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))
