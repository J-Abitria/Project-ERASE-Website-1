from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import WebsiteTheme


class AccountEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'name@example.com'})
        }


class WebsiteThemeForm(forms.ModelForm):
    class Meta:
        model = WebsiteTheme
        fields = [
            'page_background',
            'text_color',
            'surface_background',
            'surface_text',
            'header_background',
            'header_text',
            'accent_color',
            'accent_text',
        ]
        labels = {
            'page_background': _('Page background'),
            'text_color': _('Page text'),
            'surface_background': _('Content background'),
            'surface_text': _('Content text'),
            'header_background': _('Navigation and header background'),
            'header_text': _('Navigation and header text'),
            'accent_color': _('Accent and button background'),
            'accent_text': _('Accent and button text'),
        }
        widgets = {
            field: forms.TextInput(attrs={'type': 'color'})
            for field in fields
        }
