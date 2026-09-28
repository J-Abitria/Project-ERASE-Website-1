from io import BytesIO

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph

from .models import FundingEntry, WorkshopAttendance, StudentSupport, SocialMediaMetric
from .forms import FundingEntryForm, WorkshopAttendanceForm, StudentSupportForm, SocialMediaMetricForm
from .services import ReportsAnalyticsService


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin ensuring the user is staff or superuser."""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('pages:login')
        raise PermissionDenied


class ReportsDashboardView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Class-Based View for viewing and managing reporting dashboard tabs."""
    template_name = 'reports.html'
    valid_tabs = {'fundraising', 'workshops', 'students', 'social'}

    def get(self, request, *args, **kwargs):
        active_tab = request.GET.get('tab', 'fundraising')
        if active_tab not in self.valid_tabs:
            active_tab = 'fundraising'
        year_filter = request.GET.get('year', '')
        type_filter = request.GET.get('fund_type', '')
        platform_filter = request.GET.get('platform', '')

        context = {
            'funding_form': FundingEntryForm(),
            'workshop_form': WorkshopAttendanceForm(),
            'student_form': StudentSupportForm(),
            'social_form': SocialMediaMetricForm(),
            'active_tab': active_tab,
        }

        context.update(ReportsAnalyticsService.get_fundraising_data(year_filter, type_filter))
        context.update(ReportsAnalyticsService.get_workshops_data())
        context.update(ReportsAnalyticsService.get_student_support_data())
        context.update(ReportsAnalyticsService.get_social_media_data(platform_filter))

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get('form_type')
        handlers = {
            'funding': self._handle_funding,
            'workshop': self._handle_workshop,
            'student': self._handle_student,
            'social': self._handle_social,
        }

        handler = handlers.get(form_type)
        if handler:
            return handler(request)

        return redirect('pages:reports')

    def _handle_funding(self, request):
        form = FundingEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funding entry added.')
            return redirect(reverse('pages:reports') + '?tab=fundraising')
        return self._render_with_form_error(request, 'fundraising', funding_form=form)

    def _handle_workshop(self, request):
        form = WorkshopAttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Workshop record added.')
            return redirect(reverse('pages:reports') + '?tab=workshops')
        return self._render_with_form_error(request, 'workshops', workshop_form=form)

    def _handle_student(self, request):
        form = StudentSupportForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student support entry added.')
            return redirect(reverse('pages:reports') + '?tab=students')
        return self._render_with_form_error(request, 'students', student_form=form)

    def _handle_social(self, request):
        form = SocialMediaMetricForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Social media entry added.')
            return redirect(reverse('pages:reports') + '?tab=social')
        return self._render_with_form_error(request, 'social', social_form=form)

    def _render_with_form_error(self, request, tab_name, **form_overrides):
        context = {
            'funding_form': form_overrides.get('funding_form', FundingEntryForm()),
            'workshop_form': form_overrides.get('workshop_form', WorkshopAttendanceForm()),
            'student_form': form_overrides.get('student_form', StudentSupportForm()),
            'social_form': form_overrides.get('social_form', SocialMediaMetricForm()),
            'active_tab': tab_name,
        }
        context.update(ReportsAnalyticsService.get_fundraising_data())
        context.update(ReportsAnalyticsService.get_workshops_data())
        context.update(ReportsAnalyticsService.get_student_support_data())
        context.update(ReportsAnalyticsService.get_social_media_data())
        return render(request, self.template_name, context)


class ReportsPdfView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Generate a PDF for one report type and its active filters."""

    def get(self, request, *args, **kwargs):
        report_type = request.GET.get('report', 'fundraising')
        report_titles = {
            'fundraising': 'Fundraising',
            'workshops': 'Workshop Attendance',
            'students': 'Students Supported',
            'social': 'Social Media Metrics',
        }
        if report_type not in report_titles:
            return HttpResponseBadRequest('Unknown report type.')

        year_filter = request.GET.get('year', '')
        type_filter = request.GET.get('fund_type', '')
        platform_filter = request.GET.get('platform', '')

        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.45 * inch,
            leftMargin=0.45 * inch,
            topMargin=0.45 * inch,
            bottomMargin=0.45 * inch,
        )
        styles = getSampleStyleSheet()
        story = [
            Paragraph('Project ERASE — {}'.format(report_titles[report_type]), styles['Title']),
            Spacer(1, 0.2 * inch),
        ]

        if report_type == 'fundraising':
            fundraising = ReportsAnalyticsService.get_fundraising_data(year_filter, type_filter)
            story.extend([
                Paragraph(
                    'Filters: year={}; funding type={}'.format(
                        year_filter or 'All', type_filter or 'All'
                    ),
                    styles['Normal'],
                ),
                Paragraph(
                    'Total raised: ${} | Donations: ${} | Grants: ${}'.format(
                        fundraising['funding_total'],
                        fundraising['donations_total'],
                        fundraising['grants_total'],
                    ),
                    styles['Normal'],
                ),
                self._table(
                    ['Date', 'Source', 'Type', 'Amount', 'Notes'],
                    [
                        [entry.date, entry.source, entry.get_fund_type_display(), '${}'.format(entry.amount), entry.notes or '-']
                        for entry in fundraising['funding_entries']
                    ],
                ),
            ])
        elif report_type == 'workshops':
            workshops = ReportsAnalyticsService.get_workshops_data()
            story.extend([
                Paragraph(
                    'Workshops: {} | Attendees: {} | Average attendees: {}'.format(
                        workshops['workshop_count'], workshops['total_attendees'], workshops['avg_attendees']
                    ),
                    styles['Normal'],
                ),
                self._table(
                    ['Workshop', 'Date', 'Location', 'Attendees', 'Notes'],
                    [
                        [entry.workshop_name, entry.date, entry.location or '-', entry.attendee_count, entry.notes or '-']
                        for entry in workshops['workshops']
                    ],
                ),
            ])
        elif report_type == 'students':
            students = ReportsAnalyticsService.get_student_support_data()
            story.extend([
                Paragraph(
                    'Current year: {} | All-time total: {}'.format(
                        students['current_year_students'], students['all_time_students']
                    ),
                    styles['Normal'],
                ),
                self._table(
                    ['Year', 'Students Supported', 'Notes'],
                    [
                        [entry.year, entry.student_count, entry.notes or '-']
                        for entry in students['student_entries']
                    ],
                ),
            ])
        else:
            social = ReportsAnalyticsService.get_social_media_data(platform_filter)
            story.extend([
                Paragraph('Platform: {}'.format(platform_filter or 'All'), styles['Normal']),
                self._table(
                    ['Platform', 'Date', 'Followers', 'Reach', 'Likes', 'Shares', 'Comments', 'Notes'],
                    [
                        [
                            entry.get_platform_display(), entry.date, entry.followers or '-', entry.post_reach or '-',
                            entry.likes or '-', entry.shares or '-', entry.comments or '-', entry.notes or '-'
                        ]
                        for entry in social['social_entries']
                    ],
                ),
            ])
        document.build(story)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="erase-{}-report.pdf"'.format(report_type)
        return response

    @staticmethod
    def _table(headers, rows):
        table = Table([headers] + rows, repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#b8c4c8')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#eef3f4')]),
        ]))
        return table


class BaseReportDeleteView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Abstract base class for deleting report records."""
    model = None
    tab_name = 'fundraising'
    success_message = 'Entry deleted.'

    def post(self, request, pk, *args, **kwargs):
        entry = get_object_or_404(self.model, pk=pk)
        entry.delete()
        messages.success(request, self.success_message)
        return redirect(reverse('pages:reports') + f'?tab={self.tab_name}')


class DeleteFundingView(BaseReportDeleteView):
    model = FundingEntry
    tab_name = 'fundraising'
    success_message = 'Funding entry deleted.'


class DeleteWorkshopAttendanceView(BaseReportDeleteView):
    model = WorkshopAttendance
    tab_name = 'workshops'
    success_message = 'Workshop record deleted.'


class DeleteStudentSupportView(BaseReportDeleteView):
    model = StudentSupport
    tab_name = 'students'
    success_message = 'Student support entry deleted.'


class DeleteSocialMediaView(BaseReportDeleteView):
    model = SocialMediaMetric
    tab_name = 'social'
    success_message = 'Social media entry deleted.'

