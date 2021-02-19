import threading
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from rest_framework.validators import ValidationError
from dit_email_addon.api import DitEmailAddon

"""Email method for email send operations"""
def send_email_async(data):
    # contact_email = getattr(settings, 'RESET_PASSWORD', 'lokman@divine-it.net')
    # DitEmailAddon().send_email_default('lokman@divine-it.net', 'CONTACT_EMAIL', data)
    DitEmailAddon().send_email_default(data['email'], 'PASSWORD_RESET', data)


class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        try:
            threading.Thread(target=send_email_async, args=[context]).start()
        except:
            raise ValidationError({'masg':'Email not sended!'})
