from django.db import models
from django.utils.translation import gettext_lazy as _


class FundingEntry(models.Model):
    FUND_TYPE_CHOICES = [
        ('donation', _('Donation')),
        ('grant',    _('Grant')),
        ('other',    _('Other')),
    ]

    date      = models.DateField()
    source    = models.CharField(max_length=255, help_text=_('Donor or grant name'))
    fund_type = models.CharField(max_length=20, choices=FUND_TYPE_CHOICES, default='donation')
    amount    = models.DecimalField(max_digits=10, decimal_places=2)
    notes     = models.TextField(blank=True)

    class Meta:
        db_table = 'pages_fundingentry'
        ordering = ['-date']

    def __str__(self):
        return f"{self.source} ({self.get_fund_type_display()}) – ${self.amount} ({self.date})"


class WorkshopAttendance(models.Model):
    workshop_name  = models.CharField(max_length=255)
    date           = models.DateField()
    location       = models.CharField(max_length=255, blank=True)
    attendee_count = models.PositiveIntegerField(default=0)
    notes          = models.TextField(blank=True)

    class Meta:
        db_table = 'pages_workshopattendance'
        ordering = ['-date']

    def __str__(self):
        return f"{self.workshop_name} ({self.date}) – {self.attendee_count} attendees"


class StudentSupport(models.Model):
    year          = models.PositiveIntegerField()
    student_count = models.PositiveIntegerField()
    notes         = models.TextField(blank=True)

    class Meta:
        db_table = 'pages_studentsupport'
        ordering = ['-year']

    def __str__(self):
        return f"{self.year} – {self.student_count} students"


class SocialMediaMetric(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', _('Instagram')),
    ]

    platform   = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    date       = models.DateField()
    followers  = models.PositiveIntegerField(null=True, blank=True)
    post_reach = models.PositiveIntegerField(null=True, blank=True)
    likes      = models.PositiveIntegerField(null=True, blank=True)
    shares     = models.PositiveIntegerField(null=True, blank=True)
    comments   = models.PositiveIntegerField(null=True, blank=True)
    notes      = models.TextField(blank=True)
    collected_at = models.DateTimeField(auto_now_add=True)  


    class Meta:
        db_table = 'pages_socialmediametric'
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_platform_display()} – {self.date}"


class SocialMediaConnections(models.Model):
    #this will store connected platforms.
    PLATFORM_CHOICES = [
        ('instagram', _('Instagram')),
    ]

    platform   = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    connected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pages_socialmediaconnections'
        ordering = ['-connected_at']

    def __str__(self):
        return f"{self.get_platform_display()} – Connected at {self.connected_at}"

