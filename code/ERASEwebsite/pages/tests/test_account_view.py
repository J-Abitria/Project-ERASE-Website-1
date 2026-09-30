from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse


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
        self.assertEqual(response.context['role'], 'User')

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
