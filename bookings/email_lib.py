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

def send_change_status_email(fi, status):
    email_to = fi.form.emails.all().values_list('email', flat=True)
    if len(email_to) > 0:
        email_from = "info@padword.es"
        service = "{} >> {}".format(translate2("ES", fi.form.get_category.parent.name), translate2("ES", fi.form.get_category.name))
        user = "{} {}".format(fi.guest.name, fi.guest.surname)
        room = fi.guest.room
        if status.code == "01":
            subject = _("Nuevo pedido {}".format(service))
            body = _("Se ha creado el pedido {} del usuario {} (habitación {})".format(service, user, room))
        else:
            subject = _("Cambio de estado del pedido {}".format(service))
            body = _("El pedido {} del usuario {} (habitación {}) ha cambiado al estado a {}".format(service,user,room,translate2("ES",status.name)))
        url = "{}{}".format(get_domain(), reverse("bookings"))
        body += _("<br/><br/><a href='{}' target='_blank'>Pinche aquí para ver las reservas</a>".format(url))

        try:
            error = send_mail(subject, "", email_from, email_to, fail_silently=False, html_message=body)
        except Exception as e:
            print("Error (send_change_status_email): %s" % e)



