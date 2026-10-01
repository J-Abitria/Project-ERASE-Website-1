from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class SiteGuideTests(TestCase):
    def test_public_guide_lists_only_public_and_sign_in_pages(self):
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="site-guide-catalog"')
        self.assertContains(response, 'data-title-en="Events Calendar"')
        self.assertContains(response, 'href="mailto:theprojecterase@gmail.com" data-title-en="Contact"')
        self.assertContains(response, 'data-title-en="Sign In"')
        self.assertNotContains(response, 'data-title-en="Reports"')
        self.assertNotContains(response, 'data-title-en="Manage Users"')

    def test_staff_guide_includes_staff_pages_but_not_superuser_page(self):
        staff = User.objects.create_user(username='staff', password='test-password', is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(reverse('pages:home'))
        self.assertContains(response, 'data-title-en="Reports"')
        self.assertContains(response, 'data-title-en="My Account"')
        self.assertNotContains(response, 'data-title-en="Sign In"')
        self.assertNotContains(response, 'data-title-en="Manage Users"')

    def test_superuser_guide_includes_manage_users(self):
        admin = User.objects.create_superuser(username='admin', password='test-password')
        self.client.force_login(admin)
        response = self.client.get(reverse('pages:home'))
        self.assertContains(response, 'data-title-en="Manage Users"')
