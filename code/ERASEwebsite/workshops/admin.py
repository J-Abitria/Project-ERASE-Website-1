from django.contrib import admin
from .models import Shipment, Workshop


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'date', 'latitude', 'longitude', 'created_by')
    list_filter = ('date', 'city', 'created_by')
    search_fields = ('title', 'description', 'city')


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'origin_name', 'destination_name', 'status', 'status_date', 'is_published')
    list_filter = ('status', 'is_published', 'status_date')
    search_fields = ('title', 'origin_name', 'destination_name', 'contents_summary', 'partner_name')
