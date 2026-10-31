from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .models import BlogPost


class BlogPostImageDeletionTests(TestCase):
    def test_cloudinary_post_delete_removes_remote_image(self):
        if not settings.CLOUDINARY_URL:
            self.skipTest('CLOUDINARY_URL is not configured')

        author = User.objects.create_user(username='cloudinary-blog-author')
        post = BlogPost.objects.create(
            title='Cloudinary featured post',
            slug='cloudinary-featured-post',
            author=author,
            content='Post content',
            featured_image='blog/cloudinary-featured.jpg',
        )

        with patch(
            'cloudinary.uploader.destroy',
            return_value={'result': 'ok'},
        ) as destroy:
            post.delete()

        destroy.assert_called_once_with(
            'blog/cloudinary-featured.jpg',
            invalidate=True,
            resource_type='image',
        )

    def test_deleting_post_removes_featured_image_through_active_storage(self):
        author = User.objects.create_user(username='storage-blog-author')
        post = BlogPost.objects.create(
            title='Storage featured post',
            slug='storage-featured-post',
            author=author,
            content='Post content',
            featured_image='blog/stored-featured.jpg',
        )

        with patch.object(post.featured_image.storage, 'delete') as storage_delete:
            post.delete()

        storage_delete.assert_called_once_with('blog/stored-featured.jpg')

    def test_deleting_post_removes_featured_image(self):
        image_bytes = BytesIO()
        Image.new('RGB', (1, 1), color='blue').save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        author = User.objects.create_user(username='blog-author')

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                post = BlogPost.objects.create(
                    title='Featured post',
                    slug='featured-post',
                    author=author,
                    content='Post content',
                    featured_image=SimpleUploadedFile(
                        'featured.jpg',
                        image_bytes.getvalue(),
                        content_type='image/jpeg',
                    ),
                )
                image_name = post.featured_image.name
                storage = post.featured_image.storage
                self.assertTrue(storage.exists(image_name))

                BlogPost.objects.filter(pk=post.pk).delete()

                self.assertFalse(storage.exists(image_name))
