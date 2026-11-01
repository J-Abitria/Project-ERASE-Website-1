from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from event_calendar.models import Event, RSVP
from event_calendar.services import sync_completed_events
from reports.models import WorkshopAttendance


class CompletedEventSyncTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Bearer test-cron-secret'
        self.url = reverse('pages:sync_completed_events_cron')

    def create_event(self, *, scheduled_at=None, created_at=None, has_rsvp=True):
        scheduled_at = scheduled_at or self.now - timedelta(hours=1)
        event = Event.objects.create(
            title='Community workshop',
            date=scheduled_at.date(),
            time=scheduled_at.time().replace(tzinfo=None),
            description='Workshop details',
            hasRSVP=has_rsvp,
        )
        Event.objects.filter(pk=event.pk).update(created_at=created_at or scheduled_at - timedelta(days=1))
        event.refresh_from_db()
        return event

    def test_completed_rsvp_event_creates_attendance_with_sign_up_count(self):
        event = self.create_event()
        users = [
            User.objects.create_user(username=f'guest-{index}')
            for index in range(2)
        ]
        RSVP.objects.bulk_create([RSVP(event=event, user=user) for user in users])

        created_count = sync_completed_events(now=self.now)

        self.assertEqual(created_count, 1)
        attendance = WorkshopAttendance.objects.get(source_event=event)
        self.assertEqual(attendance.workshop_name, event.title)
        self.assertEqual(attendance.date, event.date)
        self.assertEqual(attendance.attendee_count, 0)
        self.assertEqual(attendance.sign_ups, 2)
        self.assertEqual(attendance.notes, event.description)

    def test_completed_event_without_rsvp_has_zero_sign_ups(self):
        event = self.create_event(has_rsvp=False)
        user = User.objects.create_user(username='guest')
        RSVP.objects.create(event=event, user=user)

        sync_completed_events(now=self.now)

        self.assertEqual(WorkshopAttendance.objects.get(source_event=event).sign_ups, 0)

    def test_future_event_is_not_synced(self):
        event = self.create_event(scheduled_at=self.now + timedelta(hours=1))

        self.assertEqual(sync_completed_events(now=self.now), 0)
        self.assertFalse(WorkshopAttendance.objects.filter(source_event=event).exists())

    def test_event_created_after_its_scheduled_time_is_not_synced(self):
        scheduled_at = self.now - timedelta(hours=1)
        event = self.create_event(scheduled_at=scheduled_at, created_at=self.now)

        self.assertEqual(sync_completed_events(now=self.now), 0)
        self.assertFalse(WorkshopAttendance.objects.filter(source_event=event).exists())

    def test_repeated_sync_does_not_duplicate_attendance(self):
        event = self.create_event()

        self.assertEqual(sync_completed_events(now=self.now), 1)
        self.assertEqual(sync_completed_events(now=self.now), 0)
        self.assertEqual(WorkshopAttendance.objects.filter(source_event=event).count(), 1)

    @override_settings(CRON_SECRET='test-cron-secret')
    def test_cron_endpoint_requires_bearer_secret_and_runs_sync(self):
        self.create_event()

        self.client.defaults['HTTP_AUTHORIZATION'] = 'Bearer wrong-secret'
        unauthorized = self.client.get(self.url)
        self.assertEqual(unauthorized.status_code, 401)

        self.client.defaults['HTTP_AUTHORIZATION'] = 'Bearer test-cron-secret'
        with patch('event_calendar.services.timezone.now', return_value=self.now):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'created': 1})

    @override_settings(CRON_SECRET='')
    def test_cron_endpoint_fails_explicitly_when_secret_is_not_configured(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 503)
