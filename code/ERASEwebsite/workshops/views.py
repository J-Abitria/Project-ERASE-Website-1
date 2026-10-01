import math

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views import View

from .forms import ShipmentForm, WorkshopForm
from .models import Shipment, Workshop


def get_workshop_or_404(raw_id):
    try:
        pk = int(raw_id)
    except (TypeError, ValueError):
        raise Http404('Workshop not found')
    return get_object_or_404(Workshop, pk=pk)


def get_shipment_or_404(raw_id):
    try:
        pk = int(raw_id)
    except (TypeError, ValueError):
        raise Http404('Journey not found')
    return get_object_or_404(Shipment, pk=pk)


def public_coordinate(value):
    return value if isinstance(value, (int, float)) and math.isfinite(value) else None


class ShipmentMapView(View):
    """Public impact map with staff-only workshop and journey management."""

    template_name = 'shipment_map.html'

    def get(self, request):
        return self.render_page(request, WorkshopForm(), ShipmentForm())

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('pages:login')
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied

        action = request.POST.get('action')
        if action == 'create_workshop':
            form = WorkshopForm(request.POST)
            shipment_form = ShipmentForm()
            editing_id = None
        elif action == 'update_workshop':
            workshop = get_workshop_or_404(request.POST.get('workshop_id'))
            form = WorkshopForm(request.POST, instance=workshop)
            shipment_form = ShipmentForm()
            editing_id = workshop.pk
        elif action == 'delete_workshop':
            workshop = get_workshop_or_404(request.POST.get('workshop_id'))
            workshop.delete()
            messages.success(request, _('Workshop location deleted.'))
            return redirect('pages:shipment_map')
        elif action in ('create_shipment', 'update_shipment'):
            instance = get_shipment_or_404(request.POST.get('shipment_id')) if action == 'update_shipment' else None
            shipment_form = ShipmentForm(request.POST, instance=instance)
            if shipment_form.is_valid():
                shipment = shipment_form.save(commit=False)
                if action == 'create_shipment':
                    shipment.created_by = request.user
                shipment.save()
                messages.success(request, _('Supply journey saved.'))
                return redirect('pages:shipment_map')
            return self.render_page(
                request, WorkshopForm(), shipment_form, shipment_editing_id=instance.pk if instance else None,
                status=400, open_form='shipment',
            )
        elif action == 'delete_shipment':
            get_shipment_or_404(request.POST.get('shipment_id')).delete()
            messages.success(request, _('Supply journey deleted.'))
            return redirect('pages:shipment_map')
        else:
            return HttpResponseBadRequest('Unknown map action.')

        if form.is_valid():
            workshop = form.save(commit=False)
            if action == 'create_workshop':
                workshop.created_by = request.user
            workshop.save()
            messages.success(request, _('Workshop location saved.'))
            return redirect('pages:shipment_map')
        return self.render_page(request, form, shipment_form, editing_id=editing_id, status=400, open_form='workshop')

    def render_page(self, request, form, shipment_form, editing_id=None, shipment_editing_id=None,
                    status=200, open_form=None):
        workshops = list(Workshop.objects.order_by('-date', '-pk'))
        can_manage_map = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
        shipments = list(Shipment.objects.all() if can_manage_map else Shipment.objects.filter(is_published=True))
        locations = [
            {
                'id': workshop.pk,
                'title': workshop.title,
                'description': workshop.description,
                'date': workshop.date.isoformat(),
                'city': workshop.city,
                'latitude': public_coordinate(workshop.latitude),
                'longitude': public_coordinate(workshop.longitude),
                'photo_url': workshop.photo.url if settings.MAP_SHOW_WORKSHOP_PHOTOS and workshop.photo else '',
            }
            for workshop in workshops
        ]
        journeys = [
            {
                'id': shipment.pk,
                'title': shipment.title,
                'origin_name': shipment.origin_name,
                'origin_latitude': public_coordinate(shipment.origin_latitude),
                'origin_longitude': public_coordinate(shipment.origin_longitude),
                'destination_name': shipment.destination_name,
                'destination_latitude': public_coordinate(shipment.destination_latitude),
                'destination_longitude': public_coordinate(shipment.destination_longitude),
                'contents_summary': shipment.contents_summary,
                'impact_summary': shipment.impact_summary,
                'partner_name': shipment.partner_name,
                'status': shipment.status,
                'status_label': shipment.get_status_display(),
                'status_date': shipment.status_date.isoformat(),
                'is_published': shipment.is_published,
            }
            for shipment in shipments
        ]
        context = {
            'form': form,
            'shipment_form': shipment_form,
            'workshops': workshops,
            'shipments': shipments,
            'cities': sorted({workshop.city for workshop in workshops if workshop.city}, key=str.casefold),
            'editing_id': editing_id,
            'shipment_editing_id': shipment_editing_id,
            'open_form': open_form,
            'can_manage_map': can_manage_map,
            'show_workshop_photos': settings.MAP_SHOW_WORKSHOP_PHOTOS,
            'map_config': {
                'locations': locations,
                'journeys': journeys,
                'style_url': settings.MAP_STYLE_URL,
            },
        }
        return render(request, self.template_name, context, status=status)
