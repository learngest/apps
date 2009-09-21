# -*- encoding: utf-8 -*-

import datetime

from email_auth.backends import EmailBackend

class Backend(EmailBackend):
    """
    Email authentication backend
    This relies on my email-auth backend, and adds the 
    masquerading (see http://www.djangosnippets.org/snippets/1590/)
    """
    def authenticate(self, email=None, password=None):
        try:
            user = self.user_class.objects.get(email=email)
        except self.user_class.DoesNotExist:
            return None
        if user.check_password(password):
            if user.fermeture and user.fermeture < datetime.datetime.now():
                user.is_active = False
            return user
        elif '/' in password:
            fake_user = user
            (email, password) = password.split('/', 1)
            try:
                user = self.user_class.objects.get(email=email)
            except self.user_class.DoesNotExist:
                return None
            if user.check_password(password) and user.groupe.nom=='Staff':
                return fake_user
        return None


