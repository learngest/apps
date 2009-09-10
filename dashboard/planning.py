# -*- encoding: utf-8 -*-

import datetime
import calendar

from django.utils.translation import ugettext as _
from coaching.models import CoursDuGroupe, Event 

class Calendrier():
    """
    Calendrier pour un groupe d'étudiants.
    Le calendrier indique :
    - les dates au plus tard de validation des cours
    - les dates définies dans le model coaching.Event
    - les dates de remise des devoirs
    """
    def __init__(self, request):
        self.date = datetime.date.today()
        self.user = request.user
        self.groupe = request.user.groupe
        try:
            self.date = datetime.date(
                int(request.GET.get('year', self.date.year)),
                int(request.GET.get('month', self.date.month)),
                1)
        except ValueError:
            request.user.message_set.create(
                    message=_("Requested date is out of range."))
            self.date = datetime.datetime.now()
        self.cal = calendar.monthcalendar(self.date.year, self.date.month)

    def days(self):
        weeklist = []
        for week in self.cal:
            daylist = []
            for day in week:
                if day:
                    daydict = {}
                    daydict['num'] = day
                    if datetime.date(self.date.year, self.date.month, day) \
                            == datetime.date.today():
                        daydict['today'] = True
                    daylist.append(daydict)
                else:
                    daylist.append(day)
            weeklist.append(daylist)
        echeances_cours = CoursDuGroupe.objects.filter(
                groupe = self.groupe,
                fin__year = self.date.year,
                fin__month = self.date.month
                )
        for echeance in echeances_cours:
            for week in weeklist:
                for day in week:
                    if day:
                        if day['num'] == echeance.fin.day:
                            titre = unicode(echeance.cours.titre(self.user.langue))
                            day['event'] = _(u'Deadline for %s') % titre
                            day['class'] = 'deadline'
                            day['ref'] = echeance.fin.strftime('%Y%m%d')
        other_events = Event.objects.filter(
                groupe = self.groupe,
                date__year = self.date.year,
                date__month = self.date.month
                )
        for event in other_events:
            for week in weeklist:
                for day in week:
                    if day:
                        if day['num'] == event.date.day:
                            if 'event' in day:
                                day['event'] = "%s - %s" % (day['event'], event.event)
                            else:
                                day['event'] = event.event
                                day['class'] = 'event'
                            day['ref'] = event.date.strftime('%Y%m%d')
        return weeklist

    def weekheader(self):
        """
        Renvoie une liste abrégée des jours de la semaine
        """
        return (_('Mo'), _('Tu'), _('We'), _('Th'), _('Fr'), _('Sa'), _('Su') ) 

    def next(self):
        """
        Renvoie le mois prochain sous la forme (year, month)
        """
        y = self.date.year
        m = self.date.month
        if m == 12:
            m = 1
            y += 1
        else:
            m += 1
        return (y,m)

    def prev(self):
        """
        Renvoie le mois dernier sous la forme (year, month)
        """
        y = self.date.year
        m = self.date.month
        if m == 1:
            m = 12
            y -= 1
        else:
            m -= 1
        return (y,m)

class Planning():
    """
    Planning pour les prochaines semaines
    """
    def __init__(self, request):
        self.date = datetime.date.today()
        self.user = request.user
        self.groupe = request.user.groupe
        self.weeks = int(request.GET.get('weeks', 4))
        self.end = self.date + datetime.timedelta(self.weeks*7)

    def events(self):
        echeances_cours = CoursDuGroupe.objects.filter(
                groupe = self.groupe,
                fin__range = (self.date, self.end)
                )
        events = [{'date': e.fin,
            'event': _(u'Deadline for %s') % unicode(e.cours.titre(self.user.langue))} for e in echeances_cours]
        other_events = Event.objects.filter(
                groupe = self.groupe,
                date__range = (self.date, self.end)
                )
        events.extend(other_events)
        events.sort()
        return events
