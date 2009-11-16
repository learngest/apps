# -*- encoding: utf-8 -*-

from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.core.mail import send_mail
from django.contrib.admin import helpers
from django.conf import settings

from coaching.forms import MailForm

def send_email(modeladmin, request, queryset):
    """
    Envoi d'email aux Utilisateurs choisis
    """
    print "entering send_email"
    dest_list = [u.get_full_name() for u in queryset]
    email_list = [request.user.email]
    email_list.extend([u.email for u in queryset])
    if request.POST.get('post'):
        print "ok post"
        f = MailForm(request.POST)
        if f.is_valid():
            print "form valide"
            send_mail(subject=f.cleaned_data['subject'],
                      message = f.cleaned_data['content'],
                      from_email=request.user.email,
                      recipient_list=email_list,
                      )
            request.user.message_set.create(
                    message=_("The message has been sent."))
            return None
        else:
            return render_to_response('coaching/sendmail.html',
                                        {'title': _('Send an email'),
                                         'from': request.user.email,
                                         'dest_list': dest_list,
                                         'form': f,
                                        },
                                        context_instance=RequestContext(request))
    else:
        print "affichage form vide"
        f = MailForm()
        return render_to_response('coaching/sendmail.html',
                                    {'title': _('Send an email'),
                            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
                            'queryset': queryset,
                            'from': request.user.email,
                            'dest_list': dest_list,
                            'form': f,
                                    },
                                    context_instance=RequestContext(request))

send_email.short_description = _('Send an email')
