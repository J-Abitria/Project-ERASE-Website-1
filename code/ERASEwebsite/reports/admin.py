from django.contrib import admin
from .models import FundingEntry, WorkshopAttendance, StudentSupport, SocialMediaMetric


@admin.register(FundingEntry)
class FundingEntryAdmin(admin.ModelAdmin):
    list_display = ('source', 'fund_type', 'amount', 'date')
    list_filter = ('fund_type', 'date')
    search_fields = ('source', 'notes')


@admin.register(WorkshopAttendance)
class WorkshopAttendanceAdmin(admin.ModelAdmin):
    list_display = ('workshop_name', 'date', 'location', 'attendee_count')
    list_filter = ('date', 'location')
    search_fields = ('workshop_name', 'location', 'notes')


@admin.register(StudentSupport)
class StudentSupportAdmin(admin.ModelAdmin):
    list_display = ('year', 'student_count')
    ordering = ('-year',)


@admin.register(SocialMediaMetric)
class SocialMediaMetricAdmin(admin.ModelAdmin):
    list_display = ('platform', 'date', 'followers', 'post_reach', 'likes', 'shares', 'comments')
    list_filter = ('platform', 'date')

