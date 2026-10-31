from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count

from .models import Event, RSVP
from .forms import EventForm
from .calendar_maker import get_calendar_data, resolve_month_year


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin ensuring the user is staff or superuser."""
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('pages:login')
        raise PermissionDenied


class CalendarView(View):
    """Class-Based View for rendering the events calendar."""
    template_name = 'calendar.html'

    def get(self, request, *args, **kwargs):
        year = request.GET.get('year')
        month = request.GET.get('month')
        current_year, current_month = resolve_month_year(year, month)

        month_events = Event.objects.filter(
            date__year=current_year, date__month=current_month
        ).order_by('date', 'time', 'pk')
        events_by_date = {}
        for event in month_events:
            events_by_date.setdefault(event.date, []).append(event)

        calendar_context = get_calendar_data(current_year, current_month, events=events_by_date)

        rsvped_ids = set()
        if request.user.is_authenticated:
            rsvped_ids = set(
                RSVP.objects.filter(user=request.user, event__in=month_events)
                .values_list('event_id', flat=True)
            )

        context = {
            **calendar_context,
            'event_form': EventForm(),
            'event_added': request.GET.get('event_added') == '1',
            'rsvped_ids': list(rsvped_ids),
            'month_events': month_events,
        }

        return render(request, self.template_name, context)


class AddEventView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Class-Based View for adding a calendar event."""
    def post(self, request, *args, **kwargs):
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            month = form.cleaned_data['date'].month
            year = form.cleaned_data['date'].year
            return redirect(f"{reverse('pages:calendar')}?month={month}&year={year}&event_added=1")
        return redirect('pages:calendar')

    def get(self, request, *args, **kwargs):
        return redirect('pages:calendar')


class RSVPEventView(LoginRequiredMixin, View):
    """Class-Based View for toggling RSVP on an event."""
    def post(self, request, event_id, *args, **kwargs):
        event = get_object_or_404(Event, pk=event_id)
        if not event.hasRSVP:
            raise PermissionDenied

        rsvp, created = RSVP.objects.get_or_create(user=request.user, event=event)
        if not created:
            rsvp.delete()

        return redirect(f"{reverse('pages:calendar')}?month={event.date.month}&year={event.date.year}")

    def get(self, request, event_id, *args, **kwargs):
        return redirect('pages:calendar')


class RSVPListingView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """Class-Based View for listing events that require RSVP."""
    template_name = 'rsvp_listing.html'
    context_object_name = 'events'

    def get_queryset(self):
        return (
            Event.objects.filter(hasRSVP=True)
            .order_by('date', 'time')
            .annotate(rsvp_count=Count('rsvps'))
        )


class RSVPDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    """Class-Based View for viewing attendees of an RSVP event."""
    template_name = 'rsvp_detail.html'
    model = Event
    pk_url_kwarg = 'event_id'
    context_object_name = 'event'

    def get_queryset(self):
        return Event.objects.filter(hasRSVP=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rsvps'] = self.object.rsvps.select_related('user').order_by('reserved_at')
        return context

