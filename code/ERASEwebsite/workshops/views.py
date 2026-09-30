import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.utils.translation import gettext as _
from .models import Workshop


class ShipmentMapView(View):
    """Class-Based View for displaying and managing workshop shipment map markers."""
    template_name = 'shipment_map.html'

    def get(self, request, *args, **kwargs):
        workshops = Workshop.objects.all()
        workshop_markers = [
            {
                'id': workshop.id,
                'title': workshop.title,
                'description': workshop.description,
                'date': workshop.date.strftime('%Y-%m-%d'),
                'city': workshop.city,
                'latitude': workshop.latitude,
                'longitude': workshop.longitude,
                'address': workshop.city,
                'photos': [workshop.photo.url] if workshop.photo else [],
            }
            for workshop in workshops
        ]

        context = {
            'workshop_markers_json': json.dumps(workshop_markers),
            'show_add_pin': request.user.is_authenticated and request.user.is_staff,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Check for AJAX delete request
        delete_workshop_id = request.POST.get('delete_workshop')
        if delete_workshop_id:
            return self._handle_delete(request, delete_workshop_id)

        # Standard POST request requires authentication and staff status
        if not (request.user.is_authenticated and request.user.is_staff):
            return redirect('pages:login')

        return self._handle_create(request)

    def _handle_delete(self, request, workshop_id):
        if not (request.user.is_authenticated and request.user.is_staff):
            return JsonResponse({'success': False, 'error': _('Authentication required')})

        try:
            workshop = Workshop.objects.get(id=int(workshop_id))
            workshop.delete()
            return JsonResponse({'success': True})
        except (Workshop.DoesNotExist, ValueError) as e:
            return JsonResponse({'success': False, 'error': _('Workshop not found')})

    def _handle_create(self, request):
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        date = request.POST.get('date')
        city = request.POST.get('city', '').strip()
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        photo = request.FILES.get('photo')

        if title and date and latitude and longitude:
            try:
                Workshop.objects.create(
                    title=title,
                    description=description,
                    date=date,
                    city=city,
                    latitude=float(latitude),
                    longitude=float(longitude),
                    photo=photo,
                    created_by=request.user,
                )
            except ValueError:
                pass

        return redirect('pages:shipment_map')

