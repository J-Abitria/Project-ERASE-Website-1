from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from workshops.models import Shipment, Workshop


class MapViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('staff', password='password', is_staff=True)
        cls.visitor = User.objects.create_user('visitor', password='password')
        cls.url = reverse('pages:shipment_map')

    def workshop_data(self, **overrides):
        data = {
            'action': 'create_workshop',
            'title': 'Reading workshop',
            'city': 'Guatemala City',
            'date': '2026-10-05',
            'description': 'Community reading event',
            'latitude': '14.6349',
            'longitude': '-90.5069',
        }
        return {**data, **overrides}

    def shipment_data(self, **overrides):
        data = {
            'action': 'create_shipment',
            'title': 'Books for schools',
            'origin_name': 'Pullman, WA',
            'origin_latitude': '46.7296',
            'origin_longitude': '-117.1817',
            'destination_name': 'Guatemala City',
            'destination_latitude': '14.6349',
            'destination_longitude': '-90.5069',
            'contents_summary': 'Donated books',
            'impact_summary': 'Supporting community reading programs',
            'partner_name': 'Community partner',
            'status': 'planned',
            'status_date': '2026-09-30',
        }
        return {**data, **overrides}

    def test_public_map_escapes_location_content(self):
        Workshop.objects.create(
            title='<script>alert(1)</script>', description='Public details',
            date=date(2026, 10, 5), city='Guatemala City',
            latitude=14.6349, longitude=-90.5069, created_by=self.staff,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertNotContains(response, 'class="edit-workshop"')
        self.assertContains(response, 'id="map-config"')

    def test_only_staff_can_mutate_locations(self):
        data = self.workshop_data()
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.client.force_login(self.visitor)
        self.assertEqual(self.client.post(self.url, data).status_code, 403)
        self.assertEqual(Workshop.objects.count(), 0)

    def test_staff_can_create_edit_and_delete_a_location(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, self.workshop_data())
        self.assertRedirects(response, self.url)
        workshop = Workshop.objects.get()
        self.assertEqual(workshop.created_by, self.staff)

        update = self.workshop_data(
            action='update_workshop', workshop_id=str(workshop.pk),
            title='Updated workshop', latitude='15.0',
        )
        self.assertRedirects(self.client.post(self.url, update), self.url)
        workshop.refresh_from_db()
        self.assertEqual(workshop.title, 'Updated workshop')
        self.assertEqual(workshop.latitude, 15.0)
        self.assertEqual(workshop.created_by, self.staff)

        self.assertRedirects(self.client.post(self.url, {
            'action': 'delete_workshop', 'workshop_id': workshop.pk,
        }), self.url)
        self.assertFalse(Workshop.objects.filter(pk=workshop.pk).exists())

    def test_invalid_coordinates_do_not_save(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, self.workshop_data(latitude='120'))
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'data-open-on-load', status_code=400)
        self.assertEqual(Workshop.objects.count(), 0)

        workshop = Workshop(
            title='Invalid', date=date(2026, 10, 5), description='',
            latitude=0, longitude=200, created_by=self.staff,
        )
        with self.assertRaises(ValidationError):
            workshop.full_clean()

    def test_deleting_creator_preserves_public_location(self):
        workshop = Workshop.objects.create(
            title='Reading workshop', description='', date=date(2026, 10, 5),
            latitude=14.6349, longitude=-90.5069, created_by=self.staff,
        )
        self.staff.delete()
        workshop.refresh_from_db()
        self.assertIsNone(workshop.created_by)

    def test_shipment_draft_is_private_until_staff_publishes(self):
        self.client.force_login(self.staff)
        self.assertRedirects(self.client.post(self.url, self.shipment_data()), self.url)
        shipment = Shipment.objects.get()
        self.assertFalse(shipment.is_published)
        self.client.logout()
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Books for schools')
        self.assertNotContains(response, 'Donated books')
        self.assertNotContains(response, 'class="edit-shipment"')

        self.client.force_login(self.staff)
        self.assertRedirects(self.client.post(self.url, self.shipment_data(
            action='update_shipment', shipment_id=str(shipment.pk), is_published='on',
            title='<script>alert(1)</script>',
        )), self.url)
        self.client.logout()
        response = self.client.get(self.url)
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, 'Donated books')
        self.assertContains(response, '"journeys"')

    def test_shipment_mutations_are_staff_only_and_validate_endpoints(self):
        self.assertEqual(self.client.post(self.url, self.shipment_data()).status_code, 302)
        self.client.force_login(self.visitor)
        self.assertEqual(self.client.post(self.url, self.shipment_data()).status_code, 403)
        self.assertEqual(Shipment.objects.count(), 0)
        self.client.force_login(self.staff)
        response = self.client.post(self.url, self.shipment_data(destination_latitude='99'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Shipment.objects.count(), 0)
        response = self.client.post(self.url, self.shipment_data(
            destination_latitude='46.7296', destination_longitude='-117.1817',
        ))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Shipment.objects.count(), 0)

    def test_staff_can_delete_shipment(self):
        self.client.force_login(self.staff)
        self.client.post(self.url, self.shipment_data(is_published='on'))
        shipment = Shipment.objects.get()
        self.assertRedirects(self.client.post(self.url, {
            'action': 'delete_shipment', 'shipment_id': shipment.pk,
        }), self.url)
        self.assertFalse(Shipment.objects.exists())
