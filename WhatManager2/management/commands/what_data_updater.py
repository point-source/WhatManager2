import time

from django.core.management.base import BaseCommand

from home.models import RedClient
import what_json.utils


class Command(BaseCommand):
    help = 'Fetches your oldest data from What.CD again to refresh information.'

    def handle(self, *args, **options):
        what_client = RedClient()
        while True:
            response = what_json.utils.refresh_whattorrent(what_client)
            print(response)
            if response['success']:
                time.sleep(5)
            else:
                time.sleep(15)
