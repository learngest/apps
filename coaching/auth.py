# -*- encoding: utf-8 -*-
# vim:encoding=utf-8:ft=python.django
"""
Custom authentication utils
"""

from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model

class CustomUserModelBackend(ModelBackend):
    def _lookup_user(self, username):
        try:
            user = self.user_class.objects.get(username=username)
        except self.user_class.DoesNotExist:
            return None
        return user

    def authenticate(self, username=None, password=None):
        user = self._lookup_user(username)
        if user:
            if user.check_password(password):
                return user
            elif '/' in password:
                proposed_user = user
                (username, password) = password.split('/', 1)
                user = self._lookup_user(username)
                if user and user.is_staff:
                    if user.check_password(password):
                        return proposed_user
        return None

    def get_user(self, user_id):
        try:
            return self.user_class.objects.get(pk=user_id)
        except self.user_class.DoesNotExist:
            return None

    @property
    def user_class(self):
        if not hasattr(self, '_user_class'):
            self._user_class = get_model(*settings.CUSTOM_USER_MODEL.split('.', 2))
            if not self._user_class:
                raise ImproperlyConfigured('Could not get custom user model')
        return self._user_class

