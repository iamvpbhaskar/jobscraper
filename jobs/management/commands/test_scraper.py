from django.core.management.base import BaseCommand
from jobs.scraper import scrape_remoteok

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        scrape_remoteok()