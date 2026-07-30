from django.core.management.base import BaseCommand
from polls.models import Question

class Command(BaseCommand):
    help = "Does something useful"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=1)

    def handle(self, *args, **options):
        qs = Question.objects.all()
        self.stdout.write(f"Questions: {qs.count()}")