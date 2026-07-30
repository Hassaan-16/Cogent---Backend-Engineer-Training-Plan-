from rest_framework import serializers

from .models import Choice, Question


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "choice_text", "votes"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(
        source="choice_set",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Question
        fields = ["id", "question_text", "pub_date", "choices"]

    def validate_question_text(self, value):
        if not value.endswith("?"):
            raise serializers.ValidationError(
                "Invalid format: A question must end with a question "
                "mark (?)."
            )

        return value


class VoteSerializer(serializers.Serializer):
    choice_id = serializers.IntegerField(
        help_text="The ID of the Choice you are voting for.",
    )
