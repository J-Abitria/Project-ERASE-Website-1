from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from reports.models import FundingEntry
from reports.services import ReportsAnalyticsService


class ReportsPdfViewTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user(username='staff', is_staff=True))
        FundingEntry.objects.create(
            date=date(2026, 1, 15),
            source='Filtered donor',
            fund_type='donation',
            amount='125.00',
        )
        FundingEntry.objects.create(
            date=date(2025, 1, 15),
            source='Excluded donor',
            fund_type='grant',
            amount='500.00',
        )

    def test_staff_can_download_filtered_pdf(self):
        with patch.object(
            ReportsAnalyticsService,
            'get_fundraising_data',
            wraps=ReportsAnalyticsService.get_fundraising_data,
        ) as fundraising_data:
            response = self.client.get(reverse('pages:reports_pdf'), {
                'year': '2026',
                'fund_type': 'donation',
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="erase-reports.pdf"', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))
        fundraising_data.assert_called_once_with('2026', 'donation')

    def test_regular_user_cannot_download_pdf(self):
        self.client.force_login(User.objects.create_user(username='regular'))

        response = self.client.get(reverse('pages:reports_pdf'))

        self.assertEqual(response.status_code, 403)