from django import forms

from .models import Question


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["question_text", "pub_date"]

    def clean_question_text(self):
        data = self.cleaned_data["question_text"]

        if not data.endswith("?"):
            raise forms.ValidationError(
                "Invalid format: A question must end with a question mark (?)."
            )

        if len(data) < 10:
            raise forms.ValidationError(
                "Question is too short. Please be more descriptive."
            )

        return data
