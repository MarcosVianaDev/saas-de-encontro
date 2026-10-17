"""Call only after authorizing access to the model that owns the storage key."""
import mimetypes
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage, default_storage
from django.http import FileResponse, Http404, HttpResponse
from django.utils.http import content_disposition_header

INTERNAL_MEDIA_PREFIX = '/_protected_media/'


def validated_key(key):
    if not isinstance(key, str) or not key or '\\' in key or ':' in key.split('/')[0]:
        raise Http404
    if any(part in {'', '.', '..'} for part in key.split('/')) or any(ord(char) < 32 or ord(char) == 127 for char in key):
        raise Http404
    return key


def local_file(key):
    """Reject escapes, directories and links; Nginx also refuses symlinks at open."""
    root = Path(default_storage.location).resolve()
    path = root
    try:
        for part in key.split('/'):
            path = path / part
            if path.is_symlink():
                raise Http404
        path = path.resolve(strict=True)
        path.relative_to(root)
        if not path.is_file():
            raise Http404
    except (OSError, ValueError, RuntimeError):
        raise Http404
    return path


def protected_media_response(key, *, as_attachment=False):
    key = validated_key(key)
    local = isinstance(default_storage, FileSystemStorage)
    if settings.MEDIA_USE_X_ACCEL_REDIRECT and (not local or
            Path(default_storage.location).resolve() != Path(settings.MEDIA_ROOT).resolve()):
        raise ImproperlyConfigured('X-Accel-Redirect exige FileSystemStorage no MEDIA_ROOT compartilhado com o Nginx.')
    if local:
        local_file(key)
    elif not default_storage.exists(key):
        raise Http404
    if settings.MEDIA_USE_X_ACCEL_REDIRECT:
        # No open()/read() and no file bytes in the application response. Escape
        # once so spaces, Unicode and literal %, # and ? remain filename data.
        filename = key.rsplit('/', 1)[-1]
        response = HttpResponse(content_type=mimetypes.guess_type(filename)[0] or 'application/octet-stream')
        response['X-Accel-Redirect'] = INTERNAL_MEDIA_PREFIX + quote(key, safe='/')
        response['Content-Disposition'] = content_disposition_header(as_attachment, filename)
    else:
        response = FileResponse(default_storage.open(key, 'rb'), as_attachment=as_attachment)
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
