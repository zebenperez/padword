from django.core.mail import send_mail

def send_email(subject, body, email_from, email_to, html_body=""):
    try:
        send_mail(subject, body, email_from, email_to, html_message=html_body, fail_silently=False)
    except Exception as e:
        print(e)

