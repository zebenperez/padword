from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _ 
from django.urls import reverse

from padword.commons import translate2

def get_domain():
    try:
        return settings.DOMAIN
    except:
        return ""

def send_change_status_email(fi, status, lang="ES"):
    email_to = fi.form.emails.all().values_list('email', flat=True)
    email_texts = fi.form.get_email_texts
    if len(email_to) > 0:
        email_from = email_texts.email_from
        service = "{} >> {}".format(translate2(lang, fi.form.get_category.parent.name), translate2(lang, fi.form.get_category.name))
        user = "{} {}".format(fi.guest.name, fi.guest.surname)
        room = fi.guest.room
        url = "{}{}".format(get_domain(), reverse("bookings"))
        if status.code == "01":
            subject = translate2(lang, email_texts.subject_new).replace("__SERVICE_NAME__", service)
            body = translate2(lang, email_texts.body_new).replace("__SERVICE_NAME__", service).replace("__USER__",user).replace("__ROOM__",room).replace("__URL__",url)
        else:
            subject = translate2(lang, email_texts.subject_change).replace("__SERVICE_NAME__", service)
            body = translate2(lang, email_texts.body_change).replace("__SERVICE_NAME__", service).replace("__USER__",user).replace("__ROOM__",room).replace("__STATUS__", translate2(lang,status.name)).replace("__URL__",url)

        try:
            for em in list(email_to):
                error = send_mail(subject, "", email_from, [em], fail_silently=False, html_message=body)
        except Exception as e:
            print("Error (send_change_status_email): %s" % e)



