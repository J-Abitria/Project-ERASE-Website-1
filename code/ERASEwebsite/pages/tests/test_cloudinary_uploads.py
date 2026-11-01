from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from blog.models import BlogPost
from pages.models import AboutProfile, WebsiteTheme


@override_settings(CLOUDINARY_URL='cloudinary://test')
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

    @patch('pages.cloudinary_uploads.cloudinary.utils.cloudinary_api_url')
    @patch('pages.cloudinary_uploads.cloudinary.utils.sign_request')
    @patch('pages.cloudinary_uploads.cloudinary.config')
    def test_master_can_request_upload_signature(self, config, sign_request, upload_url):
        config.return_value = SimpleNamespace(
            cloud_name='test-cloud',
            api_key='test-key',
            api_secret='test-secret',
            signature_algorithm='sha1',
            signature_version=2,
        )
        sign_request.return_value = {
            'timestamp': 123,
            'public_id': 'media/about/profiles/generated-id',
            'overwrite': False,
            'api_key': 'test-key',
            'signature': 'signed',
        }
        upload_url.return_value = 'https://api.cloudinary.com/v1_1/test-cloud/image/upload'
        self.client.force_login(self.master)

        response = self.client.post(
            reverse('pages:cloudinary_upload_signature'),
            {'purpose': 'about_profile'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['upload_url'], upload_url.return_value)
        self.assertEqual(response.json()['params']['signature'], 'signed')
        self.assertRegex(
            sign_request.call_args.args[0]['public_id'],
            r'^media/about/profiles/[0-9a-f]{32}$',
        )
        self.assertNotIn('overwrite', sign_request.call_args.args[0])
        self.assertEqual(sign_request.call_args.args[0]['tags'], 'media')

    @patch('pages.cloudinary_uploads.cloudinary.config')
    def test_signature_endpoint_reports_incomplete_cloudinary_credentials(self, config):
        config.return_value = SimpleNamespace(
            cloud_name='test-cloud',
            api_key='',
            api_secret='',
            signature_algorithm='sha1',
            signature_version=2,
        )
        self.client.force_login(self.master)

        response = self.client.post(
            reverse('pages:cloudinary_upload_signature'),
            {'purpose': 'about_profile'},
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn('credentials', response.json()['error'].lower())

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
        self.assertContains(about_response, 'cloudinary_upload.js?v=1')

        theme_response = self.client.get(reverse('pages:website_theme'))
        self.assertContains(theme_response, 'data-cloudinary-upload="website_logo"')

        self.client.force_login(self.staff)
        blog_response = self.client.get(reverse('blog:post_create'))
        self.assertContains(blog_response, 'data-cloudinary-upload="blog_image"')

    @patch('pages.cloudinary_uploads.cloudinary.utils.verify_api_response_signature', return_value=True)
    def test_direct_about_profile_upload_saves_verified_public_id(self, verify_signature):
        self.client.force_login(self.master)

        response = self.client.post(reverse('pages:about'), {
            'action': 'add_profile',
            'name': 'Direct Upload Member',
            'position_title': 'Director',
            'description': '',
            'direct_upload_public_id': 'media/about/profiles/profile-id',
            'direct_upload_version': '123',
            'direct_upload_signature': 'verified',
        })

        self.assertEqual(response.status_code, 302)
        profile = AboutProfile.objects.get(name='Direct Upload Member')
        self.assertEqual(profile.image.name, 'media/about/profiles/profile-id')
        verify_signature.assert_called_once_with(
            'media/about/profiles/profile-id',
            '123',
            'verified',
        )

    @patch('pages.cloudinary_uploads.cloudinary.utils.verify_api_response_signature', return_value=False)
    def test_invalid_direct_upload_signature_is_rejected(self, verify_signature):
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

    @patch('pages.cloudinary_uploads.cloudinary.utils.verify_api_response_signature', return_value=True)
    def test_direct_upload_cannot_attach_an_asset_from_another_folder(self, verify_signature):
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
        verify_signature.assert_not_called()

    @patch('pages.cloudinary_uploads.cloudinary.utils.verify_api_response_signature', return_value=True)
    def test_direct_logo_upload_saves_verified_public_id(self, verify_signature):
        self.client.force_login(self.master)

        response = self.client.post(reverse('pages:website_theme'), {
            'action': 'upload_logo',
            'direct_upload_public_id': 'media/website/logo',
            'direct_upload_version': '123',
            'direct_upload_signature': 'verified',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(WebsiteTheme.objects.get(pk=1).logo.name, 'media/website/logo')
        verify_signature.assert_called_once()

    @patch('pages.cloudinary_uploads.cloudinary.utils.verify_api_response_signature', return_value=True)
    def test_direct_blog_image_upload_saves_verified_public_id(self, verify_signature):
        self.client.force_login(self.staff)

        response = self.client.post(reverse('blog:post_create'), {
            'title': 'Direct uploaded article',
            'slug': 'direct-uploaded-article',
            'content': 'Article content',
            'direct_upload_public_id': 'media/blog/article-image',
            'direct_upload_version': '123',
            'direct_upload_signature': 'verified',
        })

        self.assertEqual(response.status_code, 302)
        article = BlogPost.objects.get(slug='direct-uploaded-article')
        self.assertEqual(article.featured_image.name, 'media/blog/article-image')
        verify_signature.assert_called_once()
