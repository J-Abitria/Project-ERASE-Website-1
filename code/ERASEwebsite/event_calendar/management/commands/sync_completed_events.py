from django.core.management.base import BaseCommand

from event_calendar.services import sync_completed_events


class Command(BaseCommand):
    help = 'Create Workshop Attendance records for eligible completed events.'

    def handle(self, *args, **options):
        created_count = sync_completed_events()
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} workshop attendance record(s).')
        )
