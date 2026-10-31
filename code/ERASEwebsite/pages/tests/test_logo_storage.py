from unittest.mock import patch

from django.conf import settings
from django.core.files.base import ContentFile
from django.test import SimpleTestCase


class WebsiteLogoCloudinaryStorageTests(SimpleTestCase):
    def test_cloudinary_upload_reuses_the_logo_public_id(self):
        if not settings.CLOUDINARY_URL:
            self.skipTest('CLOUDINARY_URL is not configured')

        from pages.models import WebsiteLogoCloudinaryStorage

        with patch(
            'pages.models.uploader.upload',
            return_value={'public_id': 'media/website/logo'},
        ) as upload:
            stored_name = WebsiteLogoCloudinaryStorage().save(
                'website/logo.png',
                ContentFile(b'image bytes'),
            )

        self.assertEqual(stored_name, 'media/website/logo')
        self.assertEqual(upload.call_args.kwargs['folder'], 'media/website')
        self.assertFalse(upload.call_args.kwargs['unique_filename'])
        self.assertTrue(upload.call_args.kwargs['overwrite'])
