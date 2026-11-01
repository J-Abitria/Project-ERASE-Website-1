from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from .models import BlogPost
from .forms import BlogPostForm
from pages.cloudinary_uploads import (
    get_verified_cloudinary_upload,
)


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('pages:login')
        raise PermissionDenied


class BlogListView(ListView):
    template_name = 'post_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return (
            BlogPost.objects
            .filter(published=True)
            .select_related('author')
        )


class BlogDetailView(DetailView):
    template_name = 'post_detail.html'
    context_object_name = 'post'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return (
            BlogPost.objects
            .filter(published=True)
            .select_related('author')
        )


class BlogManageView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    template_name = 'manage_posts.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return BlogPost.objects.select_related('author')


class BlogCreateView(LoginRequiredMixin, StaffRequiredMixin, View):
    template_name = 'post_form.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'form': BlogPostForm(),
            'page_title': 'Create Blog Post',
        })

    def post(self, request, *args, **kwargs):
        form = BlogPostForm(request.POST, request.FILES)
        image_public_id, invalid_upload = get_verified_cloudinary_upload(
            request.POST,
            'blog_image',
        )
        if invalid_upload:
            form.add_error(None, _('The image upload could not be verified. Please upload it again.'))

        if form.is_valid():
            post = form.save(commit=False)
            if image_public_id:
                post.featured_image = image_public_id
            post.author = request.user
            post.save()

            return redirect('blog:manage_posts')

        return render(request, self.template_name, {
            'form': form,
            'page_title': 'Create Blog Post',
        })


class BlogEditView(LoginRequiredMixin, StaffRequiredMixin, View):
    template_name = 'post_form.html'

    def get_post(self, slug):
        return get_object_or_404(BlogPost, slug=slug)

    def get(self, request, slug, *args, **kwargs):
        post = self.get_post(slug)

        return render(request, self.template_name, {
            'form': BlogPostForm(instance=post),
            'post': post,
            'page_title': 'Edit Blog Post',
        })

    def post(self, request, slug, *args, **kwargs):
        post = self.get_post(slug)

        form = BlogPostForm(
            request.POST,
            request.FILES,
            instance=post
        )
        image_public_id, invalid_upload = get_verified_cloudinary_upload(
            request.POST,
            'blog_image',
        )
        if invalid_upload:
            form.add_error(None, _('The image upload could not be verified. Please upload it again.'))

        if form.is_valid():
            post = form.save(commit=False)
            if image_public_id:
                post.featured_image = image_public_id
            post.save()
            return redirect('blog:manage_posts')

        return render(request, self.template_name, {
            'form': form,
            'post': post,
            'page_title': 'Edit Blog Post',
        })


class BlogDeleteView(LoginRequiredMixin, StaffRequiredMixin, View):
    template_name = 'post_confirm_delete.html'

    def get_post(self, slug):
        return get_object_or_404(BlogPost, slug=slug)

    def get(self, request, slug, *args, **kwargs):
        post = self.get_post(slug)

        return render(request, self.template_name, {
            'post': post,
        })

    def post(self, request, slug, *args, **kwargs):
        post = self.get_post(slug)
        post.delete()

        return redirect('blog:manage_posts')


class BlogPublishView(LoginRequiredMixin, StaffRequiredMixin, View):
    def post(self, request, post_id, *args, **kwargs):
        post = get_object_or_404(BlogPost, pk=post_id)

        post.published = not post.published
        post.save(update_fields=['published'])

        return redirect('blog:manage_posts')

    def get(self, request, post_id, *args, **kwargs):
        return redirect('blog:manage_posts')