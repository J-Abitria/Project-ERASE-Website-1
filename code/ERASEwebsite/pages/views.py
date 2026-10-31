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

from .forms import AboutProfileForm, AccountEmailForm, WebsiteLogoForm, WebsiteThemeForm
from .models import AboutProfile, WebsiteTheme


class HomeView(TemplateView):
    """Render the homepage."""
    template_name = 'home.html'


class AboutView(View):
    """Render the About page and let the master manage its profiles."""
    template_name = 'about.html'

    def get(self, request, *args, **kwargs):
        return self.render_page(request)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise PermissionDenied

        action = request.POST.get('action')
        if action == 'delete_profile':
            profile = get_object_or_404(AboutProfile, pk=request.POST.get('profile_id'))
            profile.delete()
            messages.success(request, _('Profile removed from the About page.'))
            return redirect('pages:about')

        if action == 'add_profile':
            form = AboutProfileForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, _('Profile added to the About page.'))
                return redirect('pages:about')
            return self.render_page(request, form=form)

        raise PermissionDenied

    def render_page(self, request, form=None):
        context = {
            'profiles': AboutProfile.objects.all(),
        }
        if request.user.is_authenticated and request.user.is_superuser:
            context['profile_form'] = form or AboutProfileForm()
        return render(request, self.template_name, context)


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


class WebsiteThemeView(LoginRequiredMixin, View):
    """Allow the master account to update the shared website palette."""
    template_name = 'website_theme.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        theme = WebsiteTheme.objects.get_or_create(pk=1)[0]
        return render(request, self.template_name, {
            'theme_form': WebsiteThemeForm(instance=theme),
            'logo_form': WebsiteLogoForm(instance=theme),
        })

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        theme = WebsiteTheme.objects.get_or_create(pk=1)[0]
        action = request.POST.get('action')
        if action == 'reset':
            theme.restore_defaults()
            messages.success(request, _('Website theme restored to the original colors.'))
            return redirect('pages:website_theme')

        if action == 'upload_logo':
            form = WebsiteLogoForm(request.POST, request.FILES, instance=theme)
            if form.is_valid():
                form.save()
                messages.success(request, _('Website logo updated successfully.'))
                return redirect('pages:website_theme')
            return render(request, self.template_name, {
                'theme_form': WebsiteThemeForm(instance=theme),
                'logo_form': form,
            })

        form = WebsiteThemeForm(request.POST, instance=theme)
        if form.is_valid():
            form.save()
            messages.success(request, _('Website theme updated successfully.'))
            return redirect('pages:website_theme')
        return render(request, self.template_name, {
            'theme_form': form,
            'logo_form': WebsiteLogoForm(instance=theme),
        })


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