from django.test import TestCase
from reports.forms import (
    FundingEntryForm,
    WorkshopAttendanceForm,
    StudentSupportForm,
    SocialMediaMetricForm,
)


class ReportFormsTests(TestCase):
    """Unit tests for reporting forms validation."""

    def test_funding_entry_form_valid(self):
        """FundingEntryForm with valid data."""
        form = FundingEntryForm(data={
            'date': '2026-03-15',
            'source': 'Community Sponsor',
            'fund_type': 'donation',
            'amount': '250.00',
            'notes': 'Quarterly contribution',
        })
        self.assertTrue(form.is_valid())

    def test_funding_entry_form_invalid_missing_fields(self):
        """FundingEntryForm requires date, source, and amount."""
        form = FundingEntryForm(data={'notes': 'Missing required fields'})
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)
        self.assertIn('source', form.errors)
        self.assertIn('amount', form.errors)

    def test_workshop_attendance_form_valid(self):
        """WorkshopAttendanceForm with valid data."""
        form = WorkshopAttendanceForm(data={
            'workshop_name': 'Web Dev 101',
            'date': '2026-04-10',
            'location': 'Library Hall',
            'attendee_count': 30,
            'notes': 'All seats filled',
        })
        self.assertTrue(form.is_valid())

    def test_workshop_attendance_form_invalid(self):
        """WorkshopAttendanceForm requires workshop_name and date."""
        form = WorkshopAttendanceForm(data={
            'location': 'Campus',
            'attendee_count': 'not-a-number',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('workshop_name', form.errors)
        self.assertIn('date', form.errors)
        self.assertIn('attendee_count', form.errors)

    def test_student_support_form_valid(self):
        """StudentSupportForm with valid year and count."""
        form = StudentSupportForm(data={
            'year': 2026,
            'student_count': 250,
            'notes': 'Expanded program reach',
        })
        self.assertTrue(form.is_valid())

    def test_student_support_form_invalid(self):
        """StudentSupportForm requires year and student_count."""
        form = StudentSupportForm(data={'notes': 'No numbers provided'})
        self.assertFalse(form.is_valid())
        self.assertIn('year', form.errors)
        self.assertIn('student_count', form.errors)

    def test_social_media_metric_form_valid(self):
        """SocialMediaMetricForm with valid platform and date."""
        form = SocialMediaMetricForm(data={
            'platform': 'instagram',
            'date': '2026-05-01',
            'followers': 1500,
            'post_reach': 3000,
            'engagement': 200,
            'notes': 'Campaign stats',
        })
        self.assertTrue(form.is_valid())

    def test_social_media_metric_form_invalid_platform(self):
        """SocialMediaMetricForm rejects invalid platform choice."""
        form = SocialMediaMetricForm(data={
            'platform': 'unsupported_platform',
            'date': '2026-05-01',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('platform', form.errors)

