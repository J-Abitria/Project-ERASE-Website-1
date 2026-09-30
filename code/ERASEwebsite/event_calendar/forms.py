from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'date', 'time', 'description', 'hasRSVP']
        labels = {
            'title': _('Title'),
            'date': _('Date'),
            'time': _('Time'),
            'description': _('Description'),
            'hasRSVP': _('Enable RSVP list?'),
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'hasRSVP': forms.CheckboxInput()
        }