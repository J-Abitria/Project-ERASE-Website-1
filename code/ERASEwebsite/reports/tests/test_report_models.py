from datetime import date
from decimal import Decimal
from django.test import TestCase
from reports.models import FundingEntry, WorkshopAttendance, StudentSupport, SocialMediaMetric


class ReportModelsTests(TestCase):
    """Unit tests for models in the reports app."""

    def test_funding_entry_str_and_ordering(self):
        """FundingEntry __str__ formatting and date ordering."""
        f1 = FundingEntry.objects.create(
            date=date(2026, 1, 15),
            source="Tech Foundation",
            fund_type="grant",
            amount=Decimal("5000.00"),
            notes="Annual tech education grant",
        )
        f2 = FundingEntry.objects.create(
            date=date(2026, 3, 20),
            source="John Doe",
            fund_type="donation",
            amount=Decimal("150.00"),
        )
        self.assertEqual(str(f1), "Tech Foundation (Grant) – $5000.00 (2026-01-15)")
        self.assertEqual(str(f2), "John Doe (Donation) – $150.00 (2026-03-20)")

        # Verify ordering: most recent date first
        entries = list(FundingEntry.objects.all())
        self.assertEqual(entries, [f2, f1])

    def test_workshop_attendance_str_and_defaults(self):
        """WorkshopAttendance __str__ formatting and default attendee count."""
        w1 = WorkshopAttendance.objects.create(
            workshop_name="Intro to Python",
            date=date(2026, 2, 10),
            location="Room 101",
            attendee_count=25,
        )
        w2 = WorkshopAttendance.objects.create(
            workshop_name="Robotics Lab",
            date=date(2026, 4, 1),
        )
        self.assertEqual(str(w1), "Intro to Python (2026-02-10) – 25 attendees")
        self.assertEqual(w2.attendee_count, 0)
        self.assertEqual(str(w2), "Robotics Lab (2026-04-01) – 0 attendees")

        # Verify ordering: -date
        workshops = list(WorkshopAttendance.objects.all())
        self.assertEqual(workshops, [w2, w1])

    def test_student_support_str_and_ordering(self):
        """StudentSupport __str__ formatting and year ordering."""
        s1 = StudentSupport.objects.create(year=2025, student_count=120)
        s2 = StudentSupport.objects.create(year=2026, student_count=180)

        self.assertEqual(str(s1), "2025 – 120 students")
        self.assertEqual(str(s2), "2026 – 180 students")

        # Verify ordering: -year
        entries = list(StudentSupport.objects.all())
        self.assertEqual(entries, [s2, s1])

    def test_social_media_metric_str_and_fields(self):
        """SocialMediaMetric __str__ formatting and optional metric values."""
        m1 = SocialMediaMetric.objects.create(
            platform="instagram",
            date=date(2026, 5, 1),
            followers=1200,
            post_reach=4500,
            engagement=350,
            notes="May campaign launch",
        )
        m2 = SocialMediaMetric.objects.create(
            platform="linkedin",
            date=date(2026, 6, 1),
        )
        self.assertEqual(str(m1), "Instagram – 2026-05-01")
        self.assertEqual(str(m2), "LinkedIn – 2026-06-01")
        self.assertIsNone(m2.followers)
        self.assertIsNone(m2.post_reach)
        self.assertIsNone(m2.engagement)

