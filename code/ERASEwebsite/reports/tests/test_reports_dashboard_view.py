from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from reports.models import FundingEntry, WorkshopAttendance, StudentSupport, SocialMediaMetric


class ReportsDashboardViewTests(TestCase):
    """Unit tests for ReportsDashboardView (access control, tab rendering, and form submissions)."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('pages:reports')

        self.normal_user = User.objects.create_user(username="normal", password="Password123!")
        self.staff_user = User.objects.create_user(username="staff", password="Password123!", is_staff=True)
        self.superuser = User.objects.create_superuser(username="super", password="Password123!")

    def test_reports_dashboard_access_control(self):
        """Anonymous user redirects to login; normal user receives 403; staff/superuser get 200."""
        # Anonymous
        anon_res = self.client.get(self.url)
        self.assertRedirects(anon_res, reverse('pages:login'))

        # Normal User
        self.client.login(username="normal", password="Password123!")
        user_res = self.client.get(self.url)
        self.assertEqual(user_res.status_code, 403)
        self.client.logout()

        # Staff User
        self.client.login(username="staff", password="Password123!")
        staff_res = self.client.get(self.url)
        self.assertEqual(staff_res.status_code, 200)
        self.assertTemplateUsed(staff_res, 'reports.html')

    def test_reports_dashboard_get_tabs_and_filters(self):
        """GET with custom active tab and filters populates context."""
        self.client.login(username="staff", password="Password123!")
        response = self.client.get(self.url, {
            'tab': 'workshops',
            'year': '2026',
            'fund_type': 'grant',
            'platform': 'instagram',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_tab'], 'workshops')
        self.assertEqual(response.context['year_filter'], '2026')
        self.assertEqual(response.context['type_filter'], 'grant')
        self.assertEqual(response.context['platform_filter'], 'instagram')

    def test_post_funding_valid_and_invalid(self):
        """POST form_type='funding' creates entry on valid input, or re-renders with errors."""
        self.client.login(username="staff", password="Password123!")

        # Valid POST
        valid_res = self.client.post(self.url, {
            'form_type': 'funding',
            'date': '2026-06-01',
            'source': 'Global Giving',
            'fund_type': 'grant',
            'amount': '3000.00',
            'notes': 'Summer grant',
        })
        self.assertRedirects(valid_res, self.url + '?tab=fundraising')
        self.assertTrue(FundingEntry.objects.filter(source='Global Giving').exists())

        # Invalid POST
        invalid_res = self.client.post(self.url, {
            'form_type': 'funding',
            'date': '',
            'source': '',
            'amount': 'not-a-number',
        })
        self.assertEqual(invalid_res.status_code, 200)
        self.assertTrue(invalid_res.context['funding_form'].errors)

    def test_post_workshop_valid_and_invalid(self):
        """POST form_type='workshop' creates record on valid input, or re-renders with errors."""
        self.client.login(username="staff", password="Password123!")

        # Valid POST
        valid_res = self.client.post(self.url, {
            'form_type': 'workshop',
            'workshop_name': 'AI in STEM',
            'date': '2026-07-15',
            'location': 'Auditorium',
            'attendee_count': 50,
            'notes': 'High engagement',
        })
        self.assertRedirects(valid_res, self.url + '?tab=workshops')
        self.assertTrue(WorkshopAttendance.objects.filter(workshop_name='AI in STEM').exists())

        # Invalid POST
        invalid_res = self.client.post(self.url, {
            'form_type': 'workshop',
            'workshop_name': '',
            'date': '',
        })
        self.assertEqual(invalid_res.status_code, 200)
        self.assertTrue(invalid_res.context['workshop_form'].errors)

    def test_post_student_valid_and_invalid(self):
        """POST form_type='student' creates record on valid input, or re-renders with errors."""
        self.client.login(username="staff", password="Password123!")

        # Valid POST
        valid_res = self.client.post(self.url, {
            'form_type': 'student',
            'year': 2026,
            'student_count': 350,
            'notes': 'Annual cohort',
        })
        self.assertRedirects(valid_res, self.url + '?tab=students')
        self.assertTrue(StudentSupport.objects.filter(year=2026, student_count=350).exists())

        # Invalid POST
        invalid_res = self.client.post(self.url, {
            'form_type': 'student',
            'year': '',
            'student_count': '',
        })
        self.assertEqual(invalid_res.status_code, 200)
        self.assertTrue(invalid_res.context['student_form'].errors)

    def test_post_social_valid_and_invalid(self):
        """POST form_type='social' creates record on valid input, or re-renders with errors."""
        self.client.login(username="staff", password="Password123!")

        # Valid POST
        valid_res = self.client.post(self.url, {
            'form_type': 'social',
            'platform': 'facebook',
            'date': '2026-08-01',
            'followers': 2500,
            'post_reach': 6000,
            'engagement': 400,
            'notes': 'Quarterly update',
        })
        self.assertRedirects(valid_res, self.url + '?tab=social')
        self.assertTrue(SocialMediaMetric.objects.filter(platform='facebook').exists())

        # Invalid POST
        invalid_res = self.client.post(self.url, {
            'form_type': 'social',
            'platform': 'unsupported',
            'date': '',
        })
        self.assertEqual(invalid_res.status_code, 200)
        self.assertTrue(invalid_res.context['social_form'].errors)

    def test_post_unknown_form_type(self):
        """POST with unrecognized form_type redirects to reports without modifying records."""
        self.client.login(username="staff", password="Password123!")
        response = self.client.post(self.url, {'form_type': 'unknown_type'})
        self.assertRedirects(response, self.url)
