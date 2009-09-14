# -*- encoding: utf-8 -*-

#from django.utils.translation import ugettext as _

class UserGranule(object):
    """
    Controller d'une granule de test pour un utilisateur
    """
    def __init__(self, user, granule):
        self.user = user
        self.granule = granule
        self.titre = self.granule.titre(self.user.langue)

    def date_validation(self):
        """
        Renvoie la date de validation du test
        False s'il n'est pas validé
        """
        #TODO
        return False

