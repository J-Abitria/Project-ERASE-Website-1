from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _


class Workshop(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    city = models.CharField(max_length=120, blank=True)
    latitude = models.FloatField(validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.FloatField(validators=[MinValueValidator(-180), MaxValueValidator(180)])
    photo = models.ImageField(upload_to='workshops/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'pages_workshop'

    def __str__(self):
        return self.title


class Shipment(models.Model):
    """A staff-reported, public supply journey; coordinates are endpoints, not tracking."""

    class Status(models.TextChoices):
        PLANNED = 'planned', _('Planned')
        IN_TRANSIT = 'in_transit', _('In transit')
        DELIVERED = 'delivered', _('Delivered')

    title = models.CharField(max_length=200)
    origin_name = models.CharField(max_length=120)
    origin_latitude = models.FloatField(validators=[MinValueValidator(-90), MaxValueValidator(90)])
    origin_longitude = models.FloatField(validators=[MinValueValidator(-180), MaxValueValidator(180)])
    destination_name = models.CharField(max_length=120)
    destination_latitude = models.FloatField(validators=[MinValueValidator(-90), MaxValueValidator(90)])
    destination_longitude = models.FloatField(validators=[MinValueValidator(-180), MaxValueValidator(180)])
    contents_summary = models.TextField()
    impact_summary = models.TextField(blank=True)
    partner_name = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLANNED)
    status_date = models.DateField()
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ('-status_date', '-pk')

    def __str__(self):
        return self.title
