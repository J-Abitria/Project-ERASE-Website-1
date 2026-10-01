from django.test import TestCase, Client
from django.urls import reverse


class StaticPagesViewTests(TestCase):
    """Unit tests for general static pages (Home and About)."""

    def setUp(self):
        self.client = Client()

    def test_home_view(self):
        """Home page loads successfully."""
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_about_view(self):
        """About page loads successfully."""
        response = self.client.get(reverse('pages:about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')
        self.assertContains(response, 'theprojecterase@gmail.com')

    def test_home_view_includes_contact_footer(self):
        response = self.client.get(reverse('pages:home'))
        self.assertContains(response, '<footer>', html=False)
        self.assertContains(response, 'theprojecterase@gmail.com')

    def test_contact_page_is_removed(self):
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 404)

