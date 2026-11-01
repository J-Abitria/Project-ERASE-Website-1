from unittest.mock import patch

import cloudinary
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from blog.models import BlogPost
from pages.models import AboutProfile, WebsiteTheme


@override_settings(CLOUDINARY_URL='cloudinary://test-key:test-secret@test-cloud')
class CloudinaryDirectUploadTests(TestCase):
    def setUp(self):
        self.master = User.objects.create_superuser(
            username='uploadmaster',
            password='Password123!',
            email='uploadmaster@example.com',
        )
        self.staff = User.objects.create_user(
            username='uploadstaff',
            password='Password123!',
            is_staff=True,
        )

    @patch('pages.cloudinary_uploads.cloudinary.config')
    @patch('pages.cloudinary_uploads.cloudinary.utils.cloudinary_api_url')
    def test_master_can_request_upload_signature(self, upload_url, config):
        upload_url.return_value = 'https://api.cloudinary.com/v1_1/test-cloud/image/upload'
        self.client.force_login(self.master)

        response = self.client.post(
            reverse('pages:cloudinary_upload_signature'),
            {'purpose': 'about_profile'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['upload_url'], upload_url.return_value)
        params = response.json()['params']
        self.assertEqual(params['api_key'], 'test-key')
        self.assertEqual(
            params['signature'],
            cloudinary.utils.api_sign_request(
                {
                    'timestamp': params['timestamp'],
                    'public_id': params['public_id'],
                    'tags': 'media',
                },
                'test-secret',
                signature_version=1,
            ),
        )
        self.assertRegex(
            params['public_id'],
            r'^media/about/profiles/[0-9a-f]{32}$',
        )
        self.assertNotIn('overwrite', params)
        self.assertEqual(params['tags'], 'media')
        config.assert_not_called()

    @patch('pages.cloudinary_uploads.cloudinary.config')
    def test_signature_endpoint_reports_incomplete_cloudinary_credentials(self, config):
        self.client.force_login(self.master)

        with override_settings(CLOUDINARY_URL='cloudinary://test-cloud'):
            response = self.client.post(
                reverse('pages:cloudinary_upload_signature'),
                {'purpose': 'about_profile'},
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn('credentials', response.json()['error'].lower())
        config.assert_not_called()

    def test_only_allowed_roles_can_request_upload_signatures(self):
        response = self.client.post(
            reverse('pages:cloudinary_upload_signature'),
            {'purpose': 'blog_image'},
        )
        self.assertEqual(response.status_code, 401)

        self.client.force_login(self.staff)
        response = self.client.post(
            reverse('pages:cloudinary_upload_signature'),
            {'purpose': 'about_profile'},
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            reverse('pages:cloudinary_upload_signature'),
            {'purpose': 'unsupported'},
        )
        self.assertEqual(response.status_code, 403)

    def test_cloudinary_forms_use_direct_upload_when_cloudinary_is_configured(self):
        self.client.force_login(self.master)

        about_response = self.client.get(reverse('pages:about'))
        self.assertContains(about_response, 'data-cloudinary-upload="about_profile"')
        self.assertContains(about_response, 'cloudinary_upload.js?v=2')

        theme_response = self.client.get(reverse('pages:website_theme'))
        self.assertContains(theme_response, 'data-cloudinary-upload="website_logo"')

        self.client.force_login(self.staff)
        blog_response = self.client.get(reverse('blog:post_create'))
        self.assertContains(blog_response, 'data-cloudinary-upload="blog_image"')

    def test_direct_about_profile_upload_saves_verified_public_id(self):
        self.client.force_login(self.master)
        public_id = 'media/about/profiles/profile-id'
        signature = self.response_signature(public_id, 123)

        response = self.client.post(reverse('pages:about'), {
            'action': 'add_profile',
            'name': 'Direct Upload Member',
            'position_title': 'Director',
            'description': '',
            'direct_upload_public_id': public_id,
            'direct_upload_version': '123',
            'direct_upload_signature': signature,
        })

        self.assertEqual(response.status_code, 302)
        profile = AboutProfile.objects.get(name='Direct Upload Member')
        self.assertEqual(profile.image.name, public_id)

    def test_invalid_direct_upload_signature_is_rejected(self):
        self.client.force_login(self.master)

        response = self.client.post(reverse('pages:about'), {
            'action': 'add_profile',
            'name': 'Unverified Member',
            'position_title': 'Director',
            'direct_upload_public_id': 'media/about/profiles/unverified',
            'direct_upload_version': '123',
            'direct_upload_signature': 'invalid',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(AboutProfile.objects.exists())
        self.assertTrue(response.context['profile_form'].non_field_errors())

    def test_direct_upload_cannot_attach_an_asset_from_another_folder(self):
        self.client.force_login(self.master)

        response = self.client.post(reverse('pages:about'), {
            'action': 'add_profile',
            'name': 'Wrong Folder Member',
            'position_title': 'Director',
            'direct_upload_public_id': 'media/blog/another-image',
            'direct_upload_version': '123',
            'direct_upload_signature': 'verified',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(AboutProfile.objects.exists())

    def test_direct_logo_upload_saves_verified_public_id(self):
        self.client.force_login(self.master)
        public_id = 'media/website/logo'

        response = self.client.post(reverse('pages:website_theme'), {
            'action': 'upload_logo',
            'direct_upload_public_id': public_id,
            'direct_upload_version': '123',
            'direct_upload_signature': self.response_signature(public_id, 123),
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(WebsiteTheme.objects.get(pk=1).logo.name, public_id)

    def test_direct_blog_image_upload_saves_verified_public_id(self):
        self.client.force_login(self.staff)
        public_id = 'media/blog/article-image'

        response = self.client.post(reverse('blog:post_create'), {
            'title': 'Direct uploaded article',
            'slug': 'direct-uploaded-article',
            'content': 'Article content',
            'direct_upload_public_id': public_id,
            'direct_upload_version': '123',
            'direct_upload_signature': self.response_signature(public_id, 123),
        })

        self.assertEqual(response.status_code, 302)
        article = BlogPost.objects.get(slug='direct-uploaded-article')
        self.assertEqual(article.featured_image.name, public_id)

    @staticmethod
    def response_signature(public_id, version):
        import cloudinary

        return cloudinary.utils.api_sign_request(
            {'public_id': public_id, 'version': version},
            'test-secret',
            signature_version=1,
        )
