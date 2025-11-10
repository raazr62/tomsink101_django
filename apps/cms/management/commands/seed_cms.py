from django.core.management.base import BaseCommand
from apps.cms.seed_data import seed_all_cms_data


class Command(BaseCommand):
    help = 'Seeds CMS data for the fitness platform'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting CMS data seeding...'))
        seed_all_cms_data()
        self.stdout.write(self.style.SUCCESS('CMS seeding completed successfully!'))
