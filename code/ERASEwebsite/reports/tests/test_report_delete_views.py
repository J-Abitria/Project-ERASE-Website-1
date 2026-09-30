from datetime import date
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from reports.models import FundingEntry, WorkshopAttendance, StudentSupport, SocialMediaMetric


class ReportDeleteViewsTests(TestCase):
    """Unit tests for report deletion views and permissions."""

    def setUp(self):
        self.client = Client()
        self.normal_user = User.objects.create_user(username="normal", password="Password123!")
        self.staff_user = User.objects.create_user(username="staff", password="Password123!", is_staff=True)

        self.funding = FundingEntry.objects.create(
            date=date(2026, 1, 1),
            source="Test Donor",
            fund_type="donation",
            amount=Decimal("100.00"),
        )
        self.workshop = WorkshopAttendance.objects.create(
            workshop_name="Test Workshop",
            date=date(2026, 2, 1),
            attendee_count=15,
        )
        self.student_support = StudentSupport.objects.create(
            year=2026,
            student_count=50,
        )
        self.social_metric = SocialMediaMetric.objects.create(
            platform="instagram",
            date=date(2026, 3, 1),
        )

    def test_delete_funding_view_staff_success(self):
        """Staff user can delete a funding entry."""
        self.client.login(username="staff", password="Password123!")
        url = reverse('pages:delete_funding', kwargs={'pk': self.funding.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('pages:reports') + '?tab=fundraising')
        self.assertFalse(FundingEntry.objects.filter(pk=self.funding.pk).exists())

    def test_delete_workshop_view_staff_success(self):
        """Staff user can delete a workshop attendance record."""
        self.client.login(username="staff", password="Password123!")
        url = reverse('pages:delete_workshop', kwargs={'pk': self.workshop.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('pages:reports') + '?tab=workshops')
        self.assertFalse(WorkshopAttendance.objects.filter(pk=self.workshop.pk).exists())

    def test_delete_student_support_view_staff_success(self):
        """Staff user can delete a student support record."""
        self.client.login(username="staff", password="Password123!")
        url = reverse('pages:delete_student', kwargs={'pk': self.student_support.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('pages:reports') + '?tab=students')
        self.assertFalse(StudentSupport.objects.filter(pk=self.student_support.pk).exists())

    def test_delete_social_media_view_staff_success(self):
        """Staff user can delete a social media metric."""
        self.client.login(username="staff", password="Password123!")
        url = reverse('pages:delete_social', kwargs={'pk': self.social_metric.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('pages:reports') + '?tab=social')
        self.assertFalse(SocialMediaMetric.objects.filter(pk=self.social_metric.pk).exists())

    def test_delete_views_forbidden_for_normal_user(self):
        """Normal user receives 403 on delete endpoints."""
        self.client.login(username="normal", password="Password123!")
        url = reverse('pages:delete_funding', kwargs={'pk': self.funding.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(FundingEntry.objects.filter(pk=self.funding.pk).exists())

    def test_delete_views_404_for_nonexistent_record(self):
        """POST to delete non-existent record returns 404."""
        self.client.login(username="staff", password="Password123!")
        url = reverse('pages:delete_funding', kwargs={'pk': 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

