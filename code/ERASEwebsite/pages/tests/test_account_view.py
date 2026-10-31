from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.core.files.base import ContentFile
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from pages.models import WebsiteTheme


class AccountViewTests(TestCase):
    """Unit tests for user account management and email updates."""

    def setUp(self):
        self.client = Client()
        self.account_url = reverse('pages:account')
        self.login_url = reverse('pages:login')

        self.normal_user = User.objects.create_user(
            username='regular',
            password='Password123!',
            email='regular@example.com'
        )
        group, _ = Group.objects.get_or_create(name='normal users')
        self.normal_user.groups.add(group)

        self.staff_user = User.objects.create_user(
            username='staffguy',
            password='Password123!',
            is_staff=True
        )

        self.superuser = User.objects.create_superuser(
            username='masteradmin',
            password='Password123!',
            email='master@example.com'
        )

    def test_account_view_requires_authentication(self):
        """Unauthenticated GET and POST requests redirect to login."""
        response_get = self.client.get(self.account_url)
        self.assertRedirects(response_get, f"{self.login_url}?next={self.account_url}")

        response_post = self.client.post(self.account_url, {'email': 'test@example.com'})
        self.assertRedirects(response_post, f"{self.login_url}?next={self.account_url}")

    def test_account_view_get_authenticated_user(self):
        """Authenticated GET loads account page with user email form and role."""
        self.client.login(username='regular', password='Password123!')
        response = self.client.get(self.account_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account.html')
        self.assertIn('email_form', response.context)
        self.assertEqual(response.context['role'], 'normal users')

    def test_account_view_role_resolution(self):
        """Test _get_user_role for superuser, staff, grouped, and standalone users."""
        # Superuser -> 'Master'
        self.client.login(username='masteradmin', password='Password123!')
        res_super = self.client.get(self.account_url)
        self.assertEqual(res_super.context['role'], 'Master')
        self.client.logout()

        # Staff -> 'Admin'
        self.client.login(username='staffguy', password='Password123!')
        res_staff = self.client.get(self.account_url)
        self.assertEqual(res_staff.context['role'], 'Admin')
        self.client.logout()

        # Plain user with no groups -> 'User'
        plain_user = User.objects.create_user(username='plain', password='Password123!')
        self.client.login(username='plain', password='Password123!')
        res_plain = self.client.get(self.account_url)
        self.assertEqual(res_plain.context['role'], 'User')

    def test_account_email_update_valid(self):
        """POST with valid email updates email and redirects to account page with success message."""
        self.client.login(username='regular', password='Password123!')
        response = self.client.post(self.account_url, {'email': 'newemail@example.com'})
        self.assertRedirects(response, self.account_url)

        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.email, 'newemail@example.com')

    def test_account_email_update_invalid(self):
        """POST with invalid email format does not update and returns errors."""
        self.client.login(username='regular', password='Password123!')
        response = self.client.post(self.account_url, {'email': 'not-an-email'})
        self.assertEqual(response.status_code, 200)

        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.email, 'regular@example.com')
        self.assertTrue(response.context['email_form'].errors)


class WebsiteThemeViewTests(TestCase):
    def setUp(self):
        self.theme_url = reverse('pages:website_theme')
        self.master = User.objects.create_superuser(
            username='themeadmin',
            password='Password123!',
            email='themeadmin@example.com',
        )
        self.regular_user = User.objects.create_user(
            username='themeuser',
            password='Password123!',
        )

    def test_theme_settings_are_master_only(self):
        self.client.login(username='themeuser', password='Password123!')
        self.assertEqual(self.client.get(self.theme_url).status_code, 403)
        self.assertEqual(
            self.client.post(self.theme_url, {'page_background': '#123456'}).status_code,
            403,
        )

    def test_master_can_update_theme_and_changes_apply_sitewide(self):
        self.client.login(username='themeadmin', password='Password123!')
        theme_page = self.client.get(self.theme_url)
        self.assertEqual(theme_page.status_code, 200)
        self.assertContains(theme_page, 'type="color"')
        self.assertContains(theme_page, 'Website Theme')
        self.assertContains(theme_page, 'Website Logo')
        self.assertContains(theme_page, 'accept=".jpg,.jpeg,.png,image/jpeg,image/png"')
        self.assertContains(theme_page, 'id="choose-logo"')
        self.assertContains(theme_page, 'name="logo"')
        self.assertContains(theme_page, 'website_logo.js')
        for extra_file_control in (
            'Currently:',
            'Clear',
            'Change:',
            'Browse',
        ):
            self.assertNotContains(theme_page, extra_file_control)

        account_page = self.client.get(reverse('pages:account'))
        self.assertNotContains(account_page, 'class="account-tabs"')
        self.assertContains(account_page, 'href="%s"' % self.theme_url)
        self.assertNotContains(theme_page, 'class="account-tabs"')

        response = self.client.post(self.theme_url, {
            'page_background': '#123456',
            'text_color': '#234567',
            'surface_background': '#345678',
            'surface_text': '#456789',
            'header_background': '#56789a',
            'header_text': '#6789ab',
            'accent_color': '#789abc',
            'accent_text': '#89abcd',
        })

        self.assertRedirects(response, self.theme_url)
        theme = WebsiteTheme.objects.get(pk=1)
        self.assertEqual(theme.page_background, '#123456')

        self.client.logout()
        response = self.client.get(reverse('pages:home'))
        self.assertContains(response, '--theme-page-background: #123456;')

        calendar_response = self.client.get(reverse('pages:calendar'))
        self.assertContains(calendar_response, 'pages/css/calendar.css?v=theme-2')
        self.assertContains(calendar_response, '--theme-header-background: #56789a;')

        blog_response = self.client.get(reverse('blog:post_list'))
        self.assertContains(blog_response, 'pages/css/blog.css?v=theme-3')

    def test_invalid_theme_color_is_not_saved(self):
        self.client.login(username='themeadmin', password='Password123!')
        theme = WebsiteTheme.objects.create(pk=1)
        response = self.client.post(self.theme_url, {
            'page_background': 'red;',
            'text_color': '#234567',
            'surface_background': '#345678',
            'surface_text': '#456789',
            'header_background': '#56789a',
            'header_text': '#6789ab',
            'accent_color': '#789abc',
            'accent_text': '#89abcd',
        })

        self.assertEqual(response.status_code, 200)
        theme.refresh_from_db()
        self.assertEqual(theme.page_background, '#ffffff')
        self.assertTrue(response.context['theme_form'].errors)

    def test_master_can_restore_original_theme_colors(self):
        self.client.login(username='themeadmin', password='Password123!')
        theme = WebsiteTheme.objects.create(
            pk=1,
            page_background='#123456',
            text_color='#234567',
            surface_background='#345678',
            surface_text='#456789',
            header_background='#56789a',
            header_text='#6789ab',
            accent_color='#789abc',
            accent_text='#89abcd',
        )

        response = self.client.post(self.theme_url, {'action': 'reset'})

        self.assertRedirects(response, self.theme_url)
        theme.refresh_from_db()
        self.assertEqual(theme.page_background, '#ffffff')
        self.assertEqual(theme.text_color, '#333333')
        self.assertEqual(theme.surface_background, '#ffffff')
        self.assertEqual(theme.surface_text, '#222222')
        self.assertEqual(theme.header_background, '#1368B8')
        self.assertEqual(theme.header_text, '#ffffff')
        self.assertEqual(theme.accent_color, '#0283FF')
        self.assertEqual(theme.accent_text, '#ffffff')

    def test_master_can_upload_site_logo(self):
        image = BytesIO()
        Image.new('RGB', (1, 1), color='blue').save(image, format='PNG')
        image.seek(0)
        self.client.login(username='themeadmin', password='Password123!')

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(self.theme_url, {
                    'action': 'upload_logo',
                    'logo': SimpleUploadedFile(
                        'site-logo.png',
                        image.read(),
                        content_type='image/png',
                    ),
                })

                self.assertRedirects(response, self.theme_url)
                theme = WebsiteTheme.objects.get(pk=1)
                self.assertEqual(theme.logo.name, 'website/logo.png')
                self.assertContains(self.client.get(reverse('pages:home')), theme.logo.url)

    def test_replacing_site_logo_deletes_old_file_and_keeps_fixed_name(self):
        image_bytes = {}
        for image_format in ('PNG', 'JPEG'):
            image = BytesIO()
            Image.new('RGB', (1, 1), color='blue').save(image, format=image_format)
            image_bytes[image_format] = image.getvalue()

        self.client.login(username='themeadmin', password='Password123!')
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                first_response = self.client.post(self.theme_url, {
                    'action': 'upload_logo',
                    'logo': SimpleUploadedFile(
                        'user-uploaded-name.png',
                        image_bytes['PNG'],
                        content_type='image/png',
                    ),
                })
                self.assertRedirects(first_response, self.theme_url)
                theme = WebsiteTheme.objects.get(pk=1)
                old_logo_name = theme.logo.name
                self.assertEqual(old_logo_name, 'website/logo.png')
                self.assertTrue(theme.logo.storage.exists(old_logo_name))
                theme.logo.storage.save(
                    'website/old-upload.png',
                    ContentFile(image_bytes['PNG']),
                )

                second_response = self.client.post(self.theme_url, {
                    'action': 'upload_logo',
                    'logo': SimpleUploadedFile(
                        'another-user-name.jpeg',
                        image_bytes['JPEG'],
                        content_type='image/jpeg',
                    ),
                })

                self.assertRedirects(second_response, self.theme_url)
                theme.refresh_from_db()
                self.assertEqual(theme.logo.name, 'website/logo.jpg')
                self.assertFalse(theme.logo.storage.exists(old_logo_name))
                self.assertTrue(theme.logo.storage.exists(theme.logo.name))
                self.assertEqual(
                    set(theme.logo.storage.listdir('website')[1]),
                    {'logo.jpg'},
                )

    def test_logo_upload_rejects_non_jpg_png_files(self):
        image = BytesIO()
        Image.new('RGB', (1, 1), color='blue').save(image, format='GIF')
        image.seek(0)
        self.client.login(username='themeadmin', password='Password123!')

        response = self.client.post(self.theme_url, {
            'action': 'upload_logo',
            'logo': SimpleUploadedFile(
                'site-logo.gif',
                image.read(),
                content_type='image/gif',
            ),
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['logo_form'].errors)
        theme = WebsiteTheme.objects.get(pk=1)
        self.assertFalse(theme.logo)

    def test_logo_upload_requires_a_file(self):
        self.client.login(username='themeadmin', password='Password123!')

        response = self.client.post(self.theme_url, {'action': 'upload_logo'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['logo_form'].errors)
