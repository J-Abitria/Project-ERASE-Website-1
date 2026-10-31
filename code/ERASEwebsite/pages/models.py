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


DEFAULT_THEME_COLORS = {
    'page_background': '#ffffff',
    'text_color': '#333333',
    'surface_background': '#ffffff',
    'surface_text': '#222222',
    'header_background': '#1368B8',
    'header_text': '#ffffff',
    'accent_color': '#0283FF',
    'accent_text': '#ffffff',
}


class WebsiteTheme(models.Model):
    """The site-wide color palette, stored as a single settings row."""
    page_background = models.CharField(
        max_length=7,
        default=DEFAULT_THEME_COLORS['page_background'],
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    text_color = models.CharField(
        max_length=7,
        default=DEFAULT_THEME_COLORS['text_color'],
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    surface_background = models.CharField(
        max_length=7,
        default=DEFAULT_THEME_COLORS['surface_background'],
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    surface_text = models.CharField(
        max_length=7,
        default=DEFAULT_THEME_COLORS['surface_text'],
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    header_background = models.CharField(
        max_length=7,
        default=DEFAULT_THEME_COLORS['header_background'],
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    header_text = models.CharField(
        max_length=7,
        default=DEFAULT_THEME_COLORS['header_text'],
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    accent_color = models.CharField(
        max_length=7,
        default=DEFAULT_THEME_COLORS['accent_color'],
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )
    accent_text = models.CharField(
        max_length=7,
        default=DEFAULT_THEME_COLORS['accent_text'],
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$')],
    )

    class Meta:
        verbose_name = 'website theme'
        verbose_name_plural = 'website theme'

    def __str__(self):
        return 'Website theme'

    def restore_defaults(self):
        for field, color in DEFAULT_THEME_COLORS.items():
            setattr(self, field, color)
        self.save()


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
