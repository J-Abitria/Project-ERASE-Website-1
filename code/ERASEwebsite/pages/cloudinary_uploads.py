from time import time
from uuid import uuid4

import cloudinary
from django.conf import settings
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST


UPLOAD_PATHS = {
    'about_profile': 'media/about/profiles/',
    'blog_image': 'media/blog/',
    'website_logo': 'media/website/logo',
}


def _can_upload(user, purpose):
    if purpose in {'about_profile', 'website_logo'}:
        return user.is_superuser
    return user.is_staff or user.is_superuser


@require_POST
def cloudinary_upload_signature(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': _('Sign in to upload an image.')}, status=401)

    purpose = request.POST.get('purpose', '')
    if purpose not in UPLOAD_PATHS or not _can_upload(request.user, purpose):
        return JsonResponse({'error': _('You are not allowed to upload this image.')}, status=403)

    config = cloudinary.config()
    if not settings.CLOUDINARY_URL or not all(
        (config.cloud_name, config.api_key, config.api_secret)
    ):
        return JsonResponse(
            {'error': _('Cloudinary credentials are not configured for this deployment.')},
            status=503,
        )

    path = UPLOAD_PATHS[purpose]
    public_id = path if purpose == 'website_logo' else f'{path}{uuid4().hex}'
    timestamp = int(time())
    params = {
        'timestamp': timestamp,
        'public_id': public_id,
        'tags': 'media',
    }
    signed_params = cloudinary.utils.sign_request(params, {
        'api_key': config.api_key,
        'api_secret': config.api_secret,
        'signature_algorithm': config.signature_algorithm,
        'signature_version': config.signature_version,
    })

    return JsonResponse({
        'upload_url': cloudinary.utils.cloudinary_api_url(
            'upload',
            cloud_name=config.cloud_name,
            resource_type='image',
        ),
        'params': signed_params,
    })


def get_verified_cloudinary_upload(post_data, purpose):
    field_names = (
        'direct_upload_public_id',
        'direct_upload_version',
        'direct_upload_signature',
    )
    values = [post_data.get(field_name, '') for field_name in field_names]
    if not any(values):
        return None, False

    path = UPLOAD_PATHS[purpose]
    public_id, version, signature = values
    if (
        not all(values)
        or not settings.CLOUDINARY_URL
        or not public_id.startswith(path)
        or (purpose == 'website_logo' and public_id != path)
        or not version.isdecimal()
    ):
        return None, True

    valid_signature = cloudinary.utils.verify_api_response_signature(
        public_id,
        version,
        signature,
    )
    return (public_id, False) if valid_signature else (None, True)


def has_cloudinary_upload_fields(post_data):
    return any(post_data.get(field_name) for field_name in (
        'direct_upload_public_id',
        'direct_upload_version',
        'direct_upload_signature',
    ))
