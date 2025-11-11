from django.core.management.base import BaseCommand
from apps.review.seed_data import seed_all_review_data


class Command(BaseCommand):
    help = 'Seed review/feedback data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting review data seeding...')
        seed_all_review_data()
        self.stdout.write(self.style.SUCCESS('Review seeding completed successfully!'))
