from datetime import date, datetime
from decimal import Decimal
from django.test import TestCase
from reports.models import FundingEntry, WorkshopAttendance, StudentSupport, SocialMediaMetric
from reports.services import ReportsAnalyticsService


class ReportAnalyticsServiceTests(TestCase):
    """Unit tests for metric aggregations and query operations in ReportsAnalyticsService."""

    def test_fundraising_data_empty(self):
        """Fundraising calculations when no entries exist."""
        data = ReportsAnalyticsService.get_fundraising_data()
        self.assertEqual(data['funding_total'], 0)
        self.assertEqual(data['donations_total'], 0)
        self.assertEqual(data['grants_total'], 0)
        self.assertEqual(data['funding_years'], [])
        self.assertEqual(data['funding_entries'].count(), 0)

    def test_fundraising_data_totals_and_filters(self):
        """Fundraising calculations with entries, year filter, and fund_type filter."""
        FundingEntry.objects.create(
            date=date(2025, 6, 1),
            source="Donor A",
            fund_type="donation",
            amount=Decimal("1000.00"),
        )
        FundingEntry.objects.create(
            date=date(2026, 2, 1),
            source="Grant B",
            fund_type="grant",
            amount=Decimal("5000.00"),
        )
        FundingEntry.objects.create(
            date=date(2026, 4, 1),
            source="Donor C",
            fund_type="donation",
            amount=Decimal("500.00"),
        )

        # Unfiltered
        data = ReportsAnalyticsService.get_fundraising_data()
        self.assertEqual(data['funding_total'], Decimal("6500.00"))
        self.assertEqual(data['donations_total'], Decimal("1500.00"))
        self.assertEqual(data['grants_total'], Decimal("5000.00"))
        self.assertEqual(data['funding_years'], [2026, 2025])
        self.assertEqual(data['funding_entries'].count(), 3)

        # Filter by year 2026
        data_2026 = ReportsAnalyticsService.get_fundraising_data(year_filter='2026')
        self.assertEqual(data_2026['funding_total'], Decimal("5500.00"))
        self.assertEqual(data_2026['donations_total'], Decimal("500.00"))
        self.assertEqual(data_2026['grants_total'], Decimal("5000.00"))
        self.assertEqual(data_2026['funding_entries'].count(), 2)

        # Filter by fund_type 'donation'
        data_donations = ReportsAnalyticsService.get_fundraising_data(type_filter='donation')
        self.assertEqual(data_donations['funding_total'], Decimal("1500.00"))
        self.assertEqual(data_donations['donations_total'], Decimal("1500.00"))
        self.assertEqual(data_donations['grants_total'], 0)
        self.assertEqual(data_donations['funding_entries'].count(), 2)

    def test_workshops_data_empty(self):
        """Workshop metrics with no workshop attendance records."""
        data = ReportsAnalyticsService.get_workshops_data()
        self.assertEqual(data['workshop_count'], 0)
        self.assertEqual(data['total_attendees'], 0)
        self.assertEqual(data['avg_attendees'], 0)

    def test_workshops_data_aggregations(self):
        """Workshop metrics with multiple records."""
        WorkshopAttendance.objects.create(
            workshop_name="Workshop 1",
            date=date(2026, 3, 1),
            attendee_count=20,
        )
        WorkshopAttendance.objects.create(
            workshop_name="Workshop 2",
            date=date(2026, 3, 15),
            attendee_count=35,
        )
        data = ReportsAnalyticsService.get_workshops_data()
        self.assertEqual(data['workshop_count'], 2)
        self.assertEqual(data['total_attendees'], 55)
        self.assertEqual(data['avg_attendees'], 27.5)

    def test_student_support_data_aggregations(self):
        """Student support totals for current year and all time."""
        current_year = datetime.now().year
        StudentSupport.objects.create(year=current_year - 1, student_count=100)
        StudentSupport.objects.create(year=current_year, student_count=150)
        StudentSupport.objects.create(year=current_year, student_count=50)

        data = ReportsAnalyticsService.get_student_support_data()
        self.assertEqual(data['current_year'], current_year)
        self.assertEqual(data['current_year_students'], 200)
        self.assertEqual(data['all_time_students'], 300)

    def test_social_media_data_and_filter(self):
        """Social media metrics query and platform filtering."""
        SocialMediaMetric.objects.create(platform='instagram', date=date(2026, 1, 1), followers=500)
        SocialMediaMetric.objects.create(platform='facebook', date=date(2026, 1, 1), followers=800)

        # Unfiltered
        data = ReportsAnalyticsService.get_social_media_data()
        self.assertEqual(data['social_entries'].count(), 2)

        # Filtered
        data_insta = ReportsAnalyticsService.get_social_media_data(platform_filter='instagram')
        self.assertEqual(data_insta['social_entries'].count(), 1)
        self.assertEqual(data_insta['social_entries'].first().platform, 'instagram')

