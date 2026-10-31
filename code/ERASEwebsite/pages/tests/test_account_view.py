from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
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
