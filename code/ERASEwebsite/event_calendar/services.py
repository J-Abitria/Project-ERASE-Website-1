from datetime import datetime

from django.db import transaction
from django.utils import timezone

from reports.models import WorkshopAttendance

from .models import Event


def sync_completed_events(now=None):
    now = now or timezone.now()
    current_timezone = timezone.get_current_timezone()
    events = Event.objects.filter(
        date__lte=timezone.localdate(now),
        attendance_record__isnull=True,
    ).order_by('date', 'time', 'pk')

    created_count = 0
    for event in events.iterator():
        scheduled_at = timezone.make_aware(
            datetime.combine(event.date, event.time),
            current_timezone,
        )
        if scheduled_at > now or event.created_at >= scheduled_at:
            continue

        with transaction.atomic():
            _, created = WorkshopAttendance.objects.get_or_create(
                source_event=event,
                defaults={
                    'workshop_name': event.title,
                    'date': event.date,
                    'attendee_count': 0,
                    'sign_ups': event.rsvps.count() if event.hasRSVP else 0,
                    'notes': event.description,
                },
            )
        created_count += int(created)

    return created_count
