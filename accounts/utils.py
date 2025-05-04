from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMessage


def detect_user(user):
    redirect_url = ''
    if user.role == 1:
        redirect_url = 'vendor-dashboard'
    elif user.role == 2:
        redirect_url = 'customer-dashboard'
    elif user.role == None and user.is_superadmin:
        redirect_url = '/admin'

    return redirect_url


def send_verification_email(request, user):
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    mail_subject = 'Activate your account.'
    message = render_to_string('accounts/emails/account_verification_email.html', {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user)
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.send()


def send_reset_password_email(request, user):
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    mail_subject = 'Reset Your Password'
    message = render_to_string('accounts/emails/reset_password_email.html', {
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user)
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.send()


def send_vendor_account_status_email(user, is_approved):
    from_email = settings.DEFAULT_FROM_EMAIL
    mail_subject = (
        'Your Vendor Account Has Been Approved'
        if is_approved else
        'Your Vendor Account Application Was Rejected'
    )
    message = render_to_string('accounts/emails/admin_approval_email.html', {
        'user': user,
        'is_approved': is_approved,
    })
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.send()
