# -*- encoding: utf-8 -*-

from django.conf import settings

def media_urls(request):
    """
    Context processor
    Returns dict with urls for medias in MEDIA
    """
    return {
        'media_url': settings.MEDIA_URL,
        'workdone': settings.WORKDONE_DIR,
    }
