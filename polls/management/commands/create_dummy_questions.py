from django.core.management.base import BaseCommand
from django.utils import timezone
from polls.models import Question


class Command(BaseCommand):
    help = 'Seeds initial dummy questions into the database'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Number of questions to create')

    def handle(self, *args, **options):
        count = options['count']
        
        # 1. Ask the database how many questions already exist
        existing_count = Question.objects.count()
        
        for i in range(1, count + 1):
            # 2. Add the loop iteration to the existing count so the number is always new
            new_number = existing_count + i 
            
            Question.objects.create(
                question_text=f'Sample Question #{new_number}',
                pub_date=timezone.now()
            )
            
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} sample questions!')
        )