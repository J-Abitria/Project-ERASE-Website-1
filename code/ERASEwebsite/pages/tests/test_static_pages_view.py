from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.test import override_settings
from django.urls import reverse

from pages.models import AboutProfile


class StaticPagesViewTests(TestCase):
    """Unit tests for general static pages (Home and About)."""

    def setUp(self):
        self.client = Client()
        self.master = User.objects.create_superuser(
            username='aboutmaster',
            password='Password123!',
            email='aboutmaster@example.com',
        )
        self.user = User.objects.create_user(
            username='aboutuser',
            password='Password123!',
        )

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

    def test_about_page_only_shows_profile_management_to_master(self):
        response = self.client.get(reverse('pages:about'))
        self.assertNotContains(response, 'open-profile-dialog')
        self.assertNotContains(response, 'role="dialog"')

        self.client.force_login(self.user)
        response = self.client.get(reverse('pages:about'))
        self.assertNotContains(response, 'open-profile-dialog')
        self.assertNotContains(response, 'role="dialog"')

        self.client.force_login(self.master)
        response = self.client.get(reverse('pages:about'))
        self.assertContains(response, 'open-profile-dialog')
        self.assertContains(response, 'about-profile-dialog')
        self.assertContains(response, 'about.css?v=2')
        self.assertContains(response, 'about_profiles.js?v=2')
        self.assertContains(response, 'Add About Page Profile')

    def test_master_can_add_and_delete_about_profile(self):
        image = BytesIO()
        Image.new('RGB', (1, 1), color='blue').save(image, format='PNG')
        image.seek(0)
        self.client.force_login(self.master)

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(reverse('pages:about'), {
                    'action': 'add_profile',
                    'image': SimpleUploadedFile(
                        'team-member.png',
                        image.getvalue(),
                        content_type='image/png',
                    ),
                    'name': 'Alex Example',
                    'position_title': 'Program Director',
                    'description': '',
                })
                self.assertRedirects(response, reverse('pages:about'))

                profile = AboutProfile.objects.get()
                self.assertEqual(profile.name, 'Alex Example')
                self.assertEqual(profile.position_title, 'Program Director')
                self.assertEqual(profile.description, '')
                self.assertTrue(profile.image.storage.exists(profile.image.name))
                self.assertContains(self.client.get(reverse('pages:about')), 'Alex Example')

                response = self.client.post(reverse('pages:about'), {
                    'action': 'delete_profile',
                    'profile_id': profile.pk,
                })
                self.assertRedirects(response, reverse('pages:about'))
                self.assertFalse(AboutProfile.objects.exists())
                self.assertFalse(profile.image.storage.exists(profile.image.name))

    def test_only_master_can_add_or_delete_about_profiles(self):
        response = self.client.post(reverse('pages:about'), {'action': 'add_profile'})
        self.assertEqual(response.status_code, 403)

        self.client.force_login(self.user)
        response = self.client.post(reverse('pages:about'), {'action': 'add_profile'})
        self.assertEqual(response.status_code, 403)

    def test_invalid_about_profile_image_is_rejected(self):
        self.client.force_login(self.master)
        response = self.client.post(reverse('pages:about'), {
            'action': 'add_profile',
            'image': SimpleUploadedFile(
                'profile.gif',
                b'not an image',
                content_type='image/gif',
            ),
            'name': 'Alex Example',
            'position_title': 'Program Director',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['profile_form'].errors)
        self.assertContains(response, 'data-open-on-load="true"')
        self.assertFalse(AboutProfile.objects.exists())
