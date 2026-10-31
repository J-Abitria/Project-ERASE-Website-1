from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blog_posts")
    content = models.TextField()
    featured_image = models.ImageField(upload_to="blog/", blank=True, null=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pages_blogpost'
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


@receiver(post_delete, sender=BlogPost)
def delete_blog_featured_image(sender, instance, **kwargs):
    if instance.featured_image:
        instance.featured_image.storage.delete(instance.featured_image.name)
