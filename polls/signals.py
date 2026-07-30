from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save

from .models import Question


@receiver(post_save, sender=Question)
def notify_new_question(sender, instance, created, **kwargs):
    """
    Signal to trigger an action whenever a Question is saved.
    'created' is a boolean that is True if a new record was inserted.
    """
    if created:
        print(
            f"SIGNAL TRIGGERED: A new poll question '{
                instance.question_text
            }' was just published!"
        )


@receiver(post_delete, sender=Question)
def notify_delete_question(sender, instance, **kwargs):
    """
    Signal to trigger an action whenever a Question is deleted.
    'deleted' is a boolean that is True if a new record was inserted.
    """
    print(
        f"SIGNAL TRIGGERED: A poll question '{
            instance.question_text
        }' was just deleted!"
    )