from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from .forms import AccountEmailForm


class HomeView(TemplateView):
    """Render the homepage."""
    template_name = 'home.html'


class AboutView(TemplateView):
    """Render the about page."""
    template_name = 'about.html'


class SignUpView(View):
    """Handle user sign-up and initial group assignment."""
    template_name = 'signup.html'

    def get(self, request, *args, **kwargs):
        form = UserCreationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            normal_users_group, _ = Group.objects.get_or_create(name='normal users')
            normal_users_group.user_set.add(user)
            return redirect('pages:login')
        return render(request, self.template_name, {'form': form})


class CustomLoginView(LoginView):
    """Custom login view."""
    template_name = 'login.html'
    redirect_authenticated_user = False


class ManageUsersView(LoginRequiredMixin, View):
    """Master account view to grant/revoke admin privileges."""
    template_name = 'manage_users.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        users = User.objects.exclude(pk=request.user.pk).order_by('username')
        return render(request, self.template_name, {'users': users})

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied

        target_id = request.POST.get('user_id')
        action = request.POST.get('action')
        target_user = get_object_or_404(User, pk=target_id)

        if not target_user.is_superuser:
            if action == 'grant':
                target_user.is_staff = True
                target_user.save()
            elif action == 'revoke':
                target_user.is_staff = False
                target_user.save()

        return redirect('pages:manage_users')


class AccountView(LoginRequiredMixin, View):
    """Display and manage current user profile and email settings."""
    template_name = 'account.html'

    def get(self, request, *args, **kwargs):
        form = AccountEmailForm(instance=request.user)
        return render(request, self.template_name, {
            'email_form': form,
            'role': self._get_user_role(request.user),
        })

    def post(self, request, *args, **kwargs):
        form = AccountEmailForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Email updated successfully.'))
            return redirect('pages:account')
        return render(request, self.template_name, {
            'email_form': form,
            'role': self._get_user_role(request.user),
        })

    def _get_user_role(self, user):
        if user.is_superuser:
            return _('Master')
        if user.is_staff:
            return _('Admin')
        groups = user.groups.values_list('name', flat=True)
        return ', '.join(groups) if groups else _('User')


class DeleteAccountView(LoginRequiredMixin, View):
    """Allow a non-superuser to delete their own account."""
    def post(self, request, *args, **kwargs):
        if request.user.is_superuser:
            raise PermissionDenied
        user = request.user
        logout(request)
        user.delete()
        return redirect('pages:home')

    def get(self, request, *args, **kwargs):
        return redirect('pages:account')


class CustomAdminView(LoginRequiredMixin, View):
    """Custom admin dashboard — accessible to staff and superusers."""
    template_name = 'custom_admin.html'

    def get(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied

        context = {
            'total_users': User.objects.count(),
            'staff_count': User.objects.filter(is_staff=True, is_superuser=False).count(),
            'superuser_count': User.objects.filter(is_superuser=True).count(),
        }
        return render(request, self.template_name, context)