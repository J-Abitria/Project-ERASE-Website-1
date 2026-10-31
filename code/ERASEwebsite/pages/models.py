"""
Pages app models.

Domain models have been refactored into dedicated apps:
- Student models -> students.models
- Workshop models -> workshops.models
- Reporting & Analytics models -> reports.models
"""
from django.core.validators import RegexValidator
from django.db import models

from students.models import Student, StudentManager, StudentQuerySet
from workshops.models import Workshop
from reports.models import FundingEntry, WorkshopAttendance, StudentSupport, SocialMediaMetric


class WebsiteTheme(models.Model):
    """The site-wide color palette, stored as a single settings row."""
    page_background = models.CharField(
        max_length=7,
        default='#ffffff',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    text_color = models.CharField(
        max_length=7,
        default='#333333',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    surface_background = models.CharField(
        max_length=7,
        default='#ffffff',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    surface_text = models.CharField(
        max_length=7,
        default='#222222',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    header_background = models.CharField(
        max_length=7,
        default='#1368B8',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    header_text = models.CharField(
        max_length=7,
        default='#ffffff',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    accent_color = models.CharField(
        max_length=7,
        default='#0283FF',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    accent_text = models.CharField(
        max_length=7,
        default='#ffffff',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )

    class Meta:
        verbose_name = 'website theme'
        verbose_name_plural = 'website theme'

    def __str__(self):
        return 'Website theme'


__all__ = [
    'Student',
    'StudentManager',
    'StudentQuerySet',
    'Workshop',
    'FundingEntry',
    'WorkshopAttendance',
    'StudentSupport',
    'SocialMediaMetric',
    'WebsiteTheme',
]
