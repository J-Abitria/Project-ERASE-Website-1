import math

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Shipment, Workshop


def clean_coordinate(value, minimum, maximum, label):
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise forms.ValidationError(
            _('Enter a %(label)s between %(minimum)s and %(maximum)s.'),
            params={'label': label, 'minimum': minimum, 'maximum': maximum},
        )
    return value


class WorkshopForm(forms.ModelForm):
    """Map editor for public workshop locations; photos need durable media storage."""

    class Meta:
        model = Workshop
        fields = ('title', 'city', 'date', 'description', 'latitude', 'longitude')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'latitude': forms.NumberInput(attrs={'step': 'any', 'min': -90, 'max': 90}),
            'longitude': forms.NumberInput(attrs={'step': 'any', 'min': -180, 'max': 180}),
        }

    def clean_latitude(self):
        return clean_coordinate(self.cleaned_data['latitude'], -90, 90, _('latitude'))

    def clean_longitude(self):
        return clean_coordinate(self.cleaned_data['longitude'], -180, 180, _('longitude'))


class ShipmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_id', 'id_shipment_%s')
        super().__init__(*args, **kwargs)

    class Meta:
        model = Shipment
        fields = (
            'title', 'origin_name', 'origin_latitude', 'origin_longitude',
            'destination_name', 'destination_latitude', 'destination_longitude',
            'contents_summary', 'impact_summary', 'partner_name',
            'status', 'status_date', 'is_published',
        )
        widgets = {
            'status_date': forms.DateInput(attrs={'type': 'date'}),
            'contents_summary': forms.Textarea(attrs={'rows': 3}),
            'impact_summary': forms.Textarea(attrs={'rows': 3}),
            **{
                name: forms.NumberInput(attrs={'step': 'any', 'min': -90 if 'latitude' in name else -180,
                                               'max': 90 if 'latitude' in name else 180})
                for name in ('origin_latitude', 'origin_longitude', 'destination_latitude', 'destination_longitude')
            },
        }

    def clean(self):
        cleaned = super().clean()
        for name in ('origin_latitude', 'destination_latitude'):
            if name in cleaned:
                try:
                    clean_coordinate(cleaned[name], -90, 90, _('latitude'))
                except forms.ValidationError as error:
                    self.add_error(name, error)
        for name in ('origin_longitude', 'destination_longitude'):
            if name in cleaned:
                try:
                    clean_coordinate(cleaned[name], -180, 180, _('longitude'))
                except forms.ValidationError as error:
                    self.add_error(name, error)
        if all(name in cleaned for name in (
            'origin_latitude', 'origin_longitude', 'destination_latitude', 'destination_longitude',
        )):
            if (cleaned['origin_latitude'], cleaned['origin_longitude']) == (
                cleaned['destination_latitude'], cleaned['destination_longitude']
            ):
                self.add_error('destination_latitude', _('Choose a destination different from the origin.'))
        return cleaned
