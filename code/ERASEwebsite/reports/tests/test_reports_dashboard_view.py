from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class ReportsDashboardInitialTabTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user(username='staff', is_staff=True))
        self.url = reverse('pages:reports')

    def test_reports_defaults_to_rendered_fundraising_tab(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_tab'], 'fundraising')
        content = response.content.decode()
        self.assertIn('id="tab-fundraising" class="tab-content active"', content)
        self.assertIn('data-initial-tab="fundraising"', content)

    def test_invalid_tab_falls_back_to_fundraising(self):
        response = self.client.get(self.url, {'tab': 'not-a-report'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_tab'], 'fundraising')
