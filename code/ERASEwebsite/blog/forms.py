from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import BlogPost


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = [
            "title",
            "slug",
            "content",
            "featured_image",
            "published",
        ]

    content = forms.CharField(
        widget=CKEditor5Widget(
            attrs={
                "class": "django_ckeditor_5",
            },
            config_name="extends",
        )
    )