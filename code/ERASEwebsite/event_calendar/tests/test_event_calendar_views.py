from datetime import date, time
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from event_calendar.models import Event, RSVP


class EventCalendarViewsTests(TestCase):
    """Tests for Calendar views and RSVP interactions."""

    def setUp(self):
        self.client = Client()
        self.normal_user = User.objects.create_user(username="normal", password="password123")
        self.staff_user = User.objects.create_user(username="staff", password="password123", is_staff=True)
        self.event = Event.objects.create(
            title="Robotics Intro",
            date=date(2026, 8, 15),
            time=time(13, 0),
            description="Robotics workshop",
            hasRSVP=True,
        )

    def test_calendar_view_get(self):
        """Test CalendarView GET request."""
        response = self.client.get(reverse('pages:calendar'), {'year': '2026', 'month': '8'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Robotics Intro")
        self.assertEqual(response.context['current_year'], 2026)
        self.assertEqual(response.context['current_month'], 8)

    def test_add_event_view_staff_required(self):
        """Test that normal users cannot add events (PermissionDenied)."""
        self.client.login(username="normal", password="password123")
        response = self.client.post(reverse('pages:add_event'), {
            'title': 'Unauthorized Event',
            'date': '2026-08-20',
            'time': '10:00',
        })
        self.assertEqual(response.status_code, 403)

    def test_mobile_agenda_uses_selected_month_in_chronological_order(self):
        morning = Event.objects.create(
            title='Morning workshop', date=self.event.date, time=time(9),
        )
        earlier = Event.objects.create(
            title='Earlier workshop', date=date(2026, 8, 2), time=time(15),
        )
        Event.objects.create(title='Next month', date=date(2026, 9, 1), time=time(9))

        response = self.client.get(reverse('pages:calendar'), {'year': 2026, 'month': 8})

        self.assertEqual(list(response.context['month_events']), [earlier, morning, self.event])
        self.assertNotContains(response, 'Next month')

    def test_mobile_agenda_empty_state_and_escaped_event_details(self):
        empty = self.client.get(reverse('pages:calendar'), {'year': 2026, 'month': 7})
        self.assertContains(empty, 'No events scheduled this month.')

        self.event.title = 'Workshop "example" <script>alert(1)</script>'
        self.event.description = '<img src=x onerror=alert(1)>'
        self.event.save()
        response = self.client.get(reverse('pages:calendar'), {'year': 2026, 'month': 8})
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertNotContains(response, '<img src=x onerror=alert(1)>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')

    def test_add_event_view_success_by_staff(self):
        """Test successful event creation by staff user."""
        self.client.login(username="staff", password="password123")
        response = self.client.post(reverse('pages:add_event'), {
            'title': 'Staff Added Event',
            'date': '2026-08-25',
            'time': '14:00',
            'description': 'Created by staff',
            'hasRSVP': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(title='Staff Added Event').exists())

    def test_rsvp_toggle(self):
        """Test RSVP toggling (create then delete on second POST)."""
        self.client.login(username="normal", password="password123")
        rsvp_url = reverse('pages:rsvp_event', kwargs={'event_id': self.event.id})

        # First POST creates RSVP
        response = self.client.post(rsvp_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(RSVP.objects.filter(event=self.event, user=self.normal_user).exists())

        # Second POST deletes RSVP
        response = self.client.post(rsvp_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(RSVP.objects.filter(event=self.event, user=self.normal_user).exists())

    def test_rsvp_listing_and_detail_views(self):
        """Test RSVP listing and detail views for staff."""
        RSVP.objects.create(event=self.event, user=self.normal_user)
        self.client.login(username="staff", password="password123")

        # Listing view
        listing_res = self.client.get(reverse('pages:rsvp_listing'))
        self.assertEqual(listing_res.status_code, 200)
        self.assertContains(listing_res, "Robotics Intro")

        # Detail view
        detail_url = reverse('pages:rsvp_detail', kwargs={'event_id': self.event.id})
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, "normal")

