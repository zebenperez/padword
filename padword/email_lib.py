from django.core.mail import send_mail

def send_email(subject, body, email_from, email_to, body_html=""):
    try:
        send_mail(subject, body, email_from, email_to, fail_silently=False)
    except Exception as e:
        print(e)

