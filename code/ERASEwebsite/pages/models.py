"""
Pages app models.

Domain models have been refactored into dedicated apps:
- Student models -> students.models
- Workshop models -> workshops.models
- Reporting & Analytics models -> reports.models
"""
from pathlib import Path

from django.core.validators import FileExtensionValidator, RegexValidator
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.deconstruct import deconstructible

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


@deconstructible
class WebsiteLogoStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            self.delete(name)
        return name

    def delete_other_logos(self, name):
        directory = str(Path(name).parent).replace('\\', '/')
        try:
            _, filenames = self.listdir(directory)
        except FileNotFoundError:
            return

        for filename in filenames:
            other_name = f'{directory}/{filename}'
            if other_name != name:
                self.delete(other_name)


def website_logo_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    if extension == '.jpeg':
        extension = '.jpg'
    return f'website/logo{extension}'


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
    logo = models.ImageField(
        upload_to=website_logo_upload_to,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        storage=WebsiteLogoStorage(),
    )

    class Meta:
        verbose_name = 'website theme'
        verbose_name_plural = 'website theme'

    def __str__(self):
        return 'Website theme'

    def save(self, *args, **kwargs):
        old_logo_name = None
        if self.pk:
            old_logo_name = type(self).objects.filter(pk=self.pk).values_list(
                'logo', flat=True
            ).first()
        logo_changed = bool(self.logo) and old_logo_name != self.logo.name

        super().save(*args, **kwargs)

        new_logo_name = self.logo.name if self.logo else None
        if old_logo_name and old_logo_name != new_logo_name:
            self.logo.storage.delete(old_logo_name)
        if logo_changed:
            self.logo.storage.delete_other_logos(new_logo_name)

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
