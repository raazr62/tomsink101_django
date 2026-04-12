from django.core.management.base import BaseCommand
from apps.cms.cache_utils import clear_cms_cache


class Command(BaseCommand):
    help = 'Clear the CMS landing page cache'

    def handle(self, *args, **options):
        clear_cms_cache()
        self.stdout.write(
            self.style.SUCCESS('Successfully cleared CMS cache')
        )
