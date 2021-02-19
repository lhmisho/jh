from django import forms
from johukum import models as jh_models
from phonenumber_field.formfields import PhoneNumberField


class MobileNumberValidationForm(forms.Form):
    mobile_number = PhoneNumberField()


class BusinessInfoFileUploadForm(forms.ModelForm):
    class Meta:
        model = jh_models.BusinessInfo
        fields = ('cover_photo', 'logo')