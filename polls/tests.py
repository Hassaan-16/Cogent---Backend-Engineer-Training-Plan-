import datetime
from unittest.mock import patch

import pytest
import factory
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from polls.models import Choice, Question

# ==============================================================================
# FACTORIES (Data Blueprints)
# ==============================================================================

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Faker('email')


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Question
    
    question_text = factory.Faker('sentence')
    pub_date = factory.LazyFunction(timezone.now)
    author = factory.SubFactory(UserFactory)


class ChoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Choice
    
    question = factory.SubFactory(QuestionFactory)
    choice_text = factory.Faker('word')
    votes = 0

# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

@pytest.mark.django_db
def test_get_questions_list_happy_path():
    """Ensure the paginated list endpoint returns a 200 OK and the correct structure."""
    QuestionFactory.create_batch(3)
    client = APIClient()
    response = client.get('/api/v1/questions/')

    assert response.status_code == status.HTTP_200_OK
    assert 'results' in response.data
    assert response.data['count'] == 3

@pytest.mark.django_db
def test_create_question_fails_if_unauthenticated():
    """Ensure anonymous users are blocked from creating data."""
    client = APIClient()
    
    response = client.post('/api/v1/questions/', {
        "question_text": "Is this working?",
        "pub_date": timezone.now()
    })
    
    assert response.status_code in [
        status.HTTP_401_UNAUTHORIZED, 
        status.HTTP_403_FORBIDDEN
    ]


@pytest.mark.django_db
def test_create_question_validation_and_error_contract():
    """
    Ensure bad data is rejected and forced into our custom error JSON shape.
    """
    user = UserFactory()
    client = APIClient()
    
    client.force_authenticate(user=user)

    response = client.post('/api/v1/questions/', {
        "question_text": "This has no question mark",
        "pub_date": timezone.now()
    })
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error_code' in response.data
    assert 'details' in response.data
    assert 'question_text' in response.data['details']


@pytest.mark.django_db
@patch('polls.views.send_vote_analytics')
def test_custom_vote_action_increments_votes(mock_analytics):
    """Ensure the @action endpoint successfully increments the choice vote count."""
    question = QuestionFactory()
    choice = ChoiceFactory(question=question, votes=0)    
    client = APIClient()

    user = UserFactory()
    client.force_authenticate(user=user)
    

    url = f'/api/v1/questions/{question.id}/vote/'
    response = client.post(url, {"choice_id": choice.id}, format='json')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == "Vote recorded successfully!"
    
    choice.refresh_from_db()

    assert choice.votes == 1


def create_question(question_text, days):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)

    return Question.objects.create(
        question_text=question_text, 
        pub_date=time
    )


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)

        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
    was_published_recently() returns False for questions whose pub_date
    is older than 1 day.
    """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)


    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = (
            timezone.now() 
            - datetime.timedelta(hours=23, minutes=59, seconds=59))
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")

        self.assertQuerySetEqual(response.context[
            "latest_question_list"], 
            []
        )

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        question = create_question(
            question_text="Past question.", 
            days=-30
        )
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertQuerySetEqual(
            response.context["latest_question_list"], 
            []
        )

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        question = create_question(
            question_text="Past question.", 
            days=-30
        )
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(
            question_text="Past question 1.", 
            days=-30
        )
        question2 = create_question(
            question_text="Past question 2.", 
            days=-5
        )
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(
            question_text="Future question.", 
            days=5
        )
        url = reverse("polls:detail", args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(
            question_text="Past Question.", 
            days=-5
        )
        url = reverse("polls:detail", args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


@pytest.mark.django_db
@patch('polls.views.send_vote_analytics') 
def test_vote_action_triggers_analytics(mock_analytics):    
    question = QuestionFactory()
    choice = ChoiceFactory(question=question, votes=0)
    
    client = APIClient()
    user = UserFactory()
    client.force_authenticate(user=user)
    
    url = f'/api/v1/questions/{question.id}/vote/'
    client.post(url, {"choice_id": choice.id}, format='json')

    mock_analytics.assert_called_once_with(choice.id)

@pytest.mark.django_db
@patch('polls.views.send_vote_analytics')
def test_regression_non_author_can_vote(mock_analytics):
    """
    REGRESSION TEST: Prevents the 403 Forbidden bug where the IsAuthorOrReadOnly 
    permission accidentally blocked non-authors from voting on a poll.
    """
    author = UserFactory()
    question = QuestionFactory(author=author)
    choice = ChoiceFactory(question=question)
    
    voter = UserFactory()
    client = APIClient()
    client.force_authenticate(user=voter)
    
    response = client.post(
        f'/api/v1/questions/{question.id}/vote/', 
        {"choice_id": choice.id}, 
        format='json'
    )
    
    assert response.status_code == status.HTTP_200_OK

    