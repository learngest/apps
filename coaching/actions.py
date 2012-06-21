# -*- encoding: utf-8 -*-

from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.core.mail import send_mail, EmailMessage
from django.contrib.admin import helpers
from django.conf import settings

from apps.coaching.forms import MailForm

def send_email(modeladmin, request, queryset):
    """
    Envoi d'email aux Utilisateurs choisis
    """
    dest_list = [u.get_full_name() for u in queryset]
    email_list = [request.user.email]
    email_list.extend([u.email for u in queryset])
    if request.POST.get('post'):
        f = MailForm(request.POST)
        if f.is_valid():
            subject = f.cleaned_data['subject']
            message = f.cleaned_data['content']
            from_email = '%s <profs@learngest.com>' % request.user.get_full_name()
            reply_to = request.user.email
            attach = None
            if 'attach' in request.FILES:
                attach = request.FILES['attach']
            try:
                mail = EmailMessage(subject=subject,
                        body=message,
                        from_email=from_email,
                        to=email_list,
                        headers={'Reply-To': reply_to})
                if attach:
                    mail.attach(attach.name, attach.read(), attach.content_type)
                mail.send()
                request.user.message_set.create(
                        message=_("The message has been sent."))
            except:
                request.user.message_set.create(
                        message=_("Error: unable to send message."))
            return None
        else:
            return render_to_response('coaching/sendmailadmin.html',
                            {'title': _('Send an email'),
                            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
                            'queryset': queryset,
                            'dest_list': dest_list,
                            'form': f,
                            },
                            context_instance=RequestContext(request))
    else:
        f = MailForm()
        return render_to_response('coaching/sendmailadmin.html',
                            {'title': _('Send an email'),
                            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
                            'queryset': queryset,
                            'dest_list': dest_list,
                            'form': f,
                            },
                            context_instance=RequestContext(request))

send_email.short_description = _('Send an email')
