import datetime
import time
import itertools
from django import forms
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.forms import BaseFormSet, formset_factory
from django.utils.text import slugify
from django_select2.forms import (HeavySelect2Widget, ModelSelect2Widget,
                                  Select2MultipleWidget, Select2Widget)
from treebeard.forms import movenodeform_factory
from embed_video.fields import EmbedVideoFormField
from johukum.models import *
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget
from zero_auth.forms import OTPValidationForm
from django.db.models import Q


class ZHOTPValidationForm(OTPValidationForm):

    def __init__(self, otp, request, mobile_no, *args, **kwargs):
        self.otp = otp
        self.request = request
        self.mobile_number = mobile_no
        super().__init__(*args, **kwargs)
        if otp is None:
            self.fields['code'] = forms.CharField(initial="Already Verified", widget=forms.TextInput(attrs={'readonly':True}))

    def clean(self):
        cleaned_data = super().clean()
        v_n = self.request.session.get('VERIFIED_MOBILE_NUMBERS', [])
        if cleaned_data['code'] != self.otp and self.mobile_number not in v_n:
            raise forms.ValidationError({
                'code': 'Invalid OTP Code'
            })
        else:
            v_n.append(self.mobile_number)
            self.request.session['VERIFIED_MOBILE_NUMBERS'] = v_n
        return cleaned_data


class CategoryForm(forms.ModelForm):
    parent = forms.ModelChoiceField(queryset=Category.objects.all(), widget=Select2Widget, required=False)
    bulk_names = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Category
        exclude = ['display_name']

    def save(self, commit=False):
        category = super().save(commit)
        category.save()
        if self.cleaned_data['bulk_names']:
            for item in self.cleaned_data['bulk_names'].split('\n'):
                if item.strip() != '':
                    Category.objects.create(
                        parent=self.cleaned_data['parent'],
                        name=item
                    )
        return category


class HoopForm(forms.ModelForm):
    class Meta:
        model = HoursOfOperation
        exclude = []


class OpenCloseForm(forms.ModelForm):

    class Meta:
        model = OpenClose
        exclude = []
        widgets = {
            'open_from': forms.TimeInput(format='%I:%M %p'),
            'open_till': forms.TimeInput(format='%I:%M %p')
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('open_24h') is True and cleaned_data.get('closed') is True:
            raise forms.ValidationError('Cannot be closed and open 24h at the same time!')
        return cleaned_data

class OCFormSet(BaseFormSet):
    def save(self, commit=False):
        hoop = HoursOfOperation(
            monday = OpenClose(**self.cleaned_data[0]),
            tuesday = OpenClose(**self.cleaned_data[1]),
            wednesday = OpenClose(**self.cleaned_data[2]),
            thursday = OpenClose(**self.cleaned_data[3]),
            friday = OpenClose(**self.cleaned_data[4]),
            saturday = OpenClose(**self.cleaned_data[5]),
            sunday = OpenClose(**self.cleaned_data[6]),
        )
        return hoop

OpenCloseFormSet = formset_factory(OpenCloseForm, formset=OCFormSet, extra=7, max_num=7)


class LocationInfoForm(forms.ModelForm):

    division = forms.ModelChoiceField(queryset=Location.get_division_queryset())

    city = forms.ModelChoiceField(queryset=Location.get_city_queryset())

    thana = forms.ModelChoiceField(queryset=Location.get_thana_queryset())


    lat = forms.FloatField(required=False)
    lon = forms.FloatField(required=False)
    street = forms.CharField(required=False)
    plus_code = forms.CharField(required=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['thana'].initial = self.instance.location
            self.fields['city'].initial = self.instance.location.parent
            self.fields['division'].initial = self.instance.location.parent.parent
            self.fields['lon'].initial = self.instance.geo['coordinates'][0]
            self.fields['lat'].initial = self.instance.geo['coordinates'][1]
        except Exception as e:
            pass

    class Meta:
        model = LocationInfo
        abstract = True
        exclude = ['geo']

    def clean(self):
        cleaned_data = super().clean()

        # #for unique plus_code checking
        # if self.instance.business_name == '' and self.data['location-plus_code'].strip() != '':
        #     if self.instance.business_name == '' and cleaned_data['plus_code'] and cleaned_data['plus_code']:
        #         if BusinessInfo.objects.filter(location={'plus_code':cleaned_data['plus_code']}).exists():
        #             raise forms.ValidationError("This plus code is already have taken")
        return cleaned_data

    def save(self, commit=False):
        loc_info = super().save(commit=False)
        loc_info.location = self.cleaned_data['thana']
        if self.cleaned_data['lat'] and self.cleaned_data['lon']:
            loc_info.geo = {
                'type': 'Point',
                'coordinates': [
                    float(self.cleaned_data['lon']),
                    float(self.cleaned_data['lat'])
                ]
            }
        return loc_info


class ContactInfoForm(forms.ModelForm):

    class Meta:
        model = ContactPersonInfo
        exclude = ['mobile_numbers']
        widgets = {
            'mobile_no': forms.TextInput(attrs={'readonly':True})
        }

    def clean(self):
        cleaned_data = super().clean()
        mobile_numbers = self.data.getlist('mobile_numbers[]')

        # if not mobile_numbers:
        #     raise forms.ValidationError('Mobile Numbers are required')
        # for unique mobile number checking
        if self.instance.name == '':
            for mn in mobile_numbers:
                if mn and mn.strip() != '':
                    if BusinessInfo.objects.mongo_find({"contact.mobile_numbers": { '$elemMatch': { 'mobile_number': { '$regex': mn } }}}).count() > 0:
                        raise forms.ValidationError("Mobile number %s already exists" % mn)

        # for unique email checking
        if self.instance.name == '' and cleaned_data['email'] and cleaned_data['email'].strip() != '':
            if BusinessInfo.objects.filter(contact={'email': cleaned_data['email']}).exists():
                raise forms.ValidationError("This email is already have taken")

        # for unique landline_no checking
        if self.instance.name == '' and cleaned_data['landline_no'] and cleaned_data['landline_no'].strip() != '':
            if BusinessInfo.objects.filter(contact={'landline_no': cleaned_data['landline_no']}).exists():
                raise forms.ValidationError("This Land Line Number is already have taken")

        # for unique fax
        if self.instance.name == '' and cleaned_data['fax_no'] and cleaned_data['fax_no'].strip() != '':
            if BusinessInfo.objects.filter(contact={'fax_no': cleaned_data['fax_no']}).exists():
                raise forms.ValidationError("This Fax Number is already have taken")
            
        if mobile_numbers:
            self.mobile_numbers =[]
            for mobile_number in mobile_numbers:
                tf = _MobileNumberHelperForm(data={'mobile_number': mobile_number})
                if not tf.is_valid():
                    raise forms.ValidationError('%s is not a valid mobile number' % mobile_number)
                self.mobile_numbers.append(tf.cleaned_data['mobile_number'])
            cleaned_data['mobile_numbers'] = set(self.mobile_numbers)
        return cleaned_data

    def save(self, commit=False):
        contact_info = super().save(commit=commit)
        numbers = []
        for mobile_number in self.cleaned_data.get('mobile_numbers', []):
            cn = ContactNumber()
            cn.mobile_number = mobile_number
            cn.verified = False
            if self.instance and self.instance.mobile_numbers:
                for contact_number in self.instance.mobile_numbers:
                    if contact_number.mobile_number == cn.mobile_number:
                        cn.verified = contact_number.verified
            numbers.append(cn)

        contact_info.mobile_numbers = numbers
        return contact_info


class HoursOfOperationForm(forms.ModelForm):

    class Meta:
        model = HoursOfOperation
        exclude = []

class AcceptedPaymentForm(forms.Form):
    accepted_payment_methods = forms.ModelMultipleChoiceField(
        queryset=PaymentMethod.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)

def year_choices():
    return [(r,r) for r in range(1700, datetime.date.today().year+1)]

def current_year():
    return datetime.date.today().year

class CompanyInfoForm(forms.ModelForm):
    professional_associations = forms.ModelMultipleChoiceField(
        queryset=ProfessionalAssociation.objects.all(), required=False, widget=Select2MultipleWidget)
    certifications = forms.ModelMultipleChoiceField(
        queryset=Certification.objects.all(), required=False, widget=Select2MultipleWidget)
    year_of_establishment = forms.ChoiceField(choices=year_choices, initial=current_year)
    description = forms.CharField(widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['professional_associations'].initial = self.instance.professional_associations.all()
            self.fields['certifications'].initial = self.instance.certifications.all()
            self.fields['description'].initial = self.instance.description
        except Exception:
            pass

    class Meta:
        model = BusinessInfo
        fields = [
            'year_of_establishment',
            'no_of_employees',
            'annual_turnover'
        ]

class CategorySelectForm(forms.Form):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(), required=True, widget=Select2MultipleWidget
    )

class UserForm(forms.ModelForm):

    GROUP = settings.AGENT_GROUP
    parent = forms.ModelChoiceField(queryset=User.objects.all(), required=False, widget=Select2Widget)
    mobile_number = PhoneNumberField(widget=PhoneNumberInternationalFallbackWidget)
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email', 'mobile_number', 'password', 'parent', 'active'
        ]
        widgets = {
            'password': forms.PasswordInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['password'] = forms.CharField(required=False, widget=forms.PasswordInput())
            self.old_password = self.instance.password

    @property
    def is_update(self):
        return hasattr(self.instance, 'pk')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('password') or cleaned_data['password'].strip() == '':
            if self.instance.pk:
                del cleaned_data['password']
            else:
                raise forms.ValidationError({
                    'password': 'Password Required'
                })
        if cleaned_data.get('mobile_number') is None:
            raise  forms.ValidationError({
                'mobile_number': 'Mobile Number is required'
            })
        mobile_number_unique_queryset = User.objects.filter(mobile_number=cleaned_data.get('mobile_number'))
        if self.is_update:
            mobile_number_unique_queryset = mobile_number_unique_queryset.filter(~Q(pk=self.instance.pk))
        if mobile_number_unique_queryset.count():
            raise forms.ValidationError({
                'mobile_number': 'Mobile Number Already Exists!'
            })
        return cleaned_data

    def save(self, commit=False):
        password = self.cleaned_data.get('password')

        user = super().save(commit)

        if password is not None:
            user.set_password(password)

        user.save()
        group, created = Group.objects.get_or_create(
            name = self.GROUP
        )
        group.user_set.add(user)
        return user


class SliderForm(forms.ModelForm):

    class Meta:
        model = Slider
        fields = '__all__'

    def clean(self):
        query = Slider.objects.all()
        if query.count() > 10:
            raise forms.ValidationError({'banner': 'You cannot input more than five banner'})


class AgentForm(UserForm):
    GROUP = settings.AGENT_GROUP
    parent = forms.ModelChoiceField(queryset=User.objects.filter(groups__name=settings.GCO_GROUP), widget=Select2Widget)


class GCOForm(UserForm):
    GROUP = settings.GCO_GROUP
    parent = forms.ModelChoiceField(queryset=User.objects.filter(groups__name=settings.MODERATOR_GROUP), required=False, widget=Select2Widget)


class ModeratorForm(UserForm):
    GROUP = settings.MODERATOR_GROUP
    parent = forms.ModelChoiceField(queryset=User.objects.filter(groups__name=settings.EDITOR_GROUP), required=False, widget=Select2Widget)


class EditorForm(UserForm):
    GROUP = settings.EDITOR_GROUP
    parent = forms.ModelChoiceField(queryset=User.objects.filter(is_superuser=True), required=False, widget=Select2Widget)


class AdminForm(UserForm):
    GROUP = settings.ADMIN_GROUP
    parent = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def save(self, commit=False):
        user = super().save(commit=commit)
        user.is_superuser = True
        user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'mobile_number', 'email', 'username', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['password'] = forms.CharField(required=False, widget=forms.PasswordInput())
            self.old_password = self.instance.password
            self.old_mobile_number = self.instance.mobile_number

    def is_number_changed(self):
        return self.old_mobile_number != self.cleaned_data['mobile_number']

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data['password'] or cleaned_data['password'].strip() == '':
            del cleaned_data['password']
        if self.instance.pk:
            mn_unique_count = User.objects.filter(mobile_number=cleaned_data['mobile_number']).exclude(pk=self.instance.pk).count()
            if mn_unique_count > 0:
                raise forms.ValidationError({
                    'mobile_number': 'Mobile Number Already Exists'
                })

        return cleaned_data

    def save(self, commit=False):
        user = super().save(commit=commit)
        password = self.cleaned_data.get('password')
        if password is not None:
            user.set_password(password)
        user.save()
        return user


class BusinessInfoModelForm(forms.ModelForm):
    class Meta:
        model = BusinessInfo
        fields = ['added_by', 'contact']


class BusinessFileUploadForm(forms.Form):

    logo = forms.ImageField(required=False)
    cover_photo = forms.ImageField(required=False)
    photo1 = forms.ImageField(required=False)
    photo2 = forms.ImageField(required=False)
    photo3 = forms.ImageField(required=False)
    photo4 = forms.ImageField(required=False)
    photo5 = forms.ImageField(required=False)
    photo6 = forms.ImageField(required=False)
    photo7 = forms.ImageField(required=False)
    photo8 = forms.ImageField(required=False)
    photo9 = forms.ImageField(required=False)
    photo10 = forms.ImageField(required=False)

    photos = forms.CharField(required=False)
    video = forms.FileField(required=False)
    embed_video = EmbedVideoFormField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        # check logo size
        if cleaned_data['logo'] and 'logo' in self.changed_data and cleaned_data['logo'].size > settings.LOGO_MAX_SIZE:
            raise forms.ValidationError({
                'logo': 'Maximum size of logo cannot excced %d KB' % (settings.LOGO_MAX_SIZE / 1024)
            })

        # check cover size
        if cleaned_data['cover_photo'] and 'logo' in self.changed_data and cleaned_data['cover_photo'].size > settings.COVER_MAX_SIZE:
            raise forms.ValidationError({
                'cover_photo': 'Maximum size of cover photo cannot excced %d KB' % (settings.COVER_MAX_SIZE / 1024)
            })

        photo_fields = ['photo1', 'photo2', 'photo3', 'photo4', 'photo5', 'photo6', 'photo7', 'photo8', 'photo9', 'photo10']
        for photo_field in photo_fields:
            if cleaned_data[photo_field] and photo_field in self.changed_data and cleaned_data[photo_field].size > settings.PHOTOS_MAX_SIZE:
                raise forms.ValidationError({
                    photo_field: 'Maximum size of photo cannot be over %d KB' % (settings.PHOTOS_MAX_SIZE / 1024)
                })

        if cleaned_data['video']:
            if cleaned_data['video'].size > settings.VIDEOS_MAX_SIZE:
                raise forms.ValidationError({
                    'video': 'Maximum size of a video cannot excced %d MB' % (settings.VIDEOS_MAX_SIZE / 1024 / 1024)
                })
            # if cleaned_data['video'].content_type not in settings.ALLOWED_VIDEO_CONTENT_TYPES:
            #     raise forms.ValidationError({
            #         'video': 'This video format is not supported. Supported formats are %s' % (', '.join(settings.ALLOWED_VIDEO_CONTENT_TYPES))
            #     })

        return cleaned_data

    def build_name(self, new_pref, old_name):
        return '%s_%s.%s' % (new_pref, time.strftime("%Y%m%d_%H%M%S"), old_name.split('.')[1])

    def save(self, business_info, update=False):

        business_name = slugify(business_info.location.business_name)
        if self.cleaned_data['logo']:
            business_info.logo.save(self.build_name('%s_logo' % business_name, self.cleaned_data['logo'].name), self.cleaned_data['logo'])
        elif update and self.cleaned_data['logo'] is False:
            business_info.logo.delete()

        if self.cleaned_data['cover_photo']:
            business_info.cover_photo.save(self.build_name('%s_cover_photo' % business_name, self.cleaned_data['cover_photo'].name), self.cleaned_data['cover_photo'])
        elif update and self.cleaned_data['cover_photo'] is False:
            business_info.cover_photo.delete()

        for video in business_info.videos.all():
            business_info.videos.remove(video)
            video.delete()

        if self.cleaned_data['video']:
            uploaded_video = UploadedVideo.objects.create()
            uploaded_video.video.save(self.build_name('%s_video' % business_name, self.cleaned_data['video'].name), self.cleaned_data['video'])
            business_info.videos.add(uploaded_video)


        photos = []

        if self.cleaned_data['photo1']:
            p1 = UploadedImage.objects.create()
            p1.image.save(self.build_name(business_name, self.cleaned_data['photo1'].name), self.cleaned_data['photo1'])
            p1.save()
            photos.append(p1)


        if self.cleaned_data['photo2']:
            p2 = UploadedImage.objects.create()
            p2.image.save(self.build_name(business_name, self.cleaned_data['photo2'].name), self.cleaned_data['photo2'])
            p2.save()
            photos.append(p2)

        if self.cleaned_data['photo3']:
            p3 = UploadedImage.objects.create()
            p3.image.save(self.build_name(business_name, self.cleaned_data['photo3'].name), self.cleaned_data['photo3'])
            p3.save()
            photos.append(p3)

        if self.cleaned_data['photo4']:
            p4 = UploadedImage.objects.create()
            p4.image.save(self.build_name(business_name, self.cleaned_data['photo4'].name), self.cleaned_data['photo4'])
            p4.save()
            photos.append(p4)

        if self.cleaned_data['photo5']:
            p5 = UploadedImage.objects.create()
            p5.image.save(self.build_name(business_name, self.cleaned_data['photo5'].name), self.cleaned_data['photo5'])
            p5.save()
            photos.append(p5)

        if self.cleaned_data['photo6']:
            p6 = UploadedImage.objects.create()
            p6.image.save(self.build_name(business_name, self.cleaned_data['photo6'].name), self.cleaned_data['photo6'])
            p6.save()
            photos.append(p6)

        if self.cleaned_data['photo7']:
            p7 = UploadedImage.objects.create()
            p7.image.save(self.build_name(business_name, self.cleaned_data['photo7'].name), self.cleaned_data['photo7'])
            p7.save()
            photos.append(p7)

        if self.cleaned_data['photo8']:
            p8 = UploadedImage.objects.create()
            p8.image.save(self.build_name(business_name, self.cleaned_data['photo8'].name), self.cleaned_data['photo8'])
            p8.save()
            photos.append(p8)

        if self.cleaned_data['photo9']:
            p9 = UploadedImage.objects.create()
            p9.image.save(self.build_name(business_name, self.cleaned_data['photo9'].name), self.cleaned_data['photo9'])
            p9.save()
            photos.append(p9)

        if self.cleaned_data['photo10']:
            p10 = UploadedImage.objects.create()
            p10.image.save(self.build_name(business_name, self.cleaned_data['photo10'].name), self.cleaned_data['photo10'])
            p10.save()
            photos.append(p10)

        for photo in business_info.photos.all():
            business_info.photos.remove(photo)
            photo.delete()

        for photo in photos:
            business_info.photos.add(photo)

        if self.cleaned_data['embed_video']:
            business_info.embed_video = self.cleaned_data['embed_video']


class MobileDataChangeStatusForm(forms.Form):
    mobile_data_id = forms.CharField(widget=forms.HiddenInput())
    status = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        try:
            self.mobile_data = MobileNumberData.objects.get(pk=cleaned_data['mobile_data_id'])
        except Exception:
            raise forms.ValidationError('Invalid mobile data!')

        if int(cleaned_data['status']) not in [MobileNumberData.APPROVED, MobileNumberData.PENDING, MobileNumberData.REVIEWED, MobileNumberData.REJECTED]:
            raise forms.ValidationError('Invalid Status for mobile data')

        return cleaned_data

    def update_status(self, request):
        self.mobile_data.status = int(self.cleaned_data['status'])
        if self.mobile_data.status == MobileNumberData.APPROVED:
            self.mobile_data.approved_by = request.user
            self.mobile_data.approved_at = datetime.datetime.now()
        if self.mobile_data.status == MobileNumberData.REVIEWED:
            self.mobile_data.reviewed_by = request.user
            self.mobile_data.reviewed_at = datetime.datetime.now()
        if self.mobile_data.status == MobileNumberData.REJECTED:
            self.mobile_data.rejected_by = request.user
            self.mobile_data.rejected_at = datetime.datetime.now()
        self.mobile_data.edit_by = request.user
        self.mobile_data.save()


class ChangeStatusForm(forms.Form):
    business_info_id = forms.CharField(widget=forms.HiddenInput())
    status = forms.IntegerField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        try:
            self.business_info = BusinessInfo.objects.get(pk=cleaned_data['business_info_id'])
        except Exception:
            raise forms.ValidationError('Invalid Business Info')

        if cleaned_data['status'] not in [BusinessInfo.PENDING, BusinessInfo.REVIEWED, BusinessInfo.REJECTED, BusinessInfo.APPROVED]:
            raise forms.ValidationError('Invalid Status for business info')

        return cleaned_data

    def update_status(self, request):
        self.business_info.status = self.cleaned_data['status']
        if self.business_info.status == BusinessInfo.APPROVED:
            self.business_info.approved_by = request.user
            self.business_info.approved_at = datetime.datetime.now()
        elif self.business_info.status == BusinessInfo.REVIEWED:
            self.business_info.reviewed_by = request.user
            self.business_info.reviewed_at = datetime.datetime.now()
        elif self.business_info.status == BusinessInfo.REJECTED:
            self.business_info.rejected_by = request.user
            self.business_info.rejected_at = datetime.datetime.now()
        self.business_info.edit_by = request.user  # saving the last edit person
        self.business_info.save()


class _MobileNumberHelperForm(forms.Form):
    mobile_number = PhoneNumberField()


class _LandLineNumberHyperForm(forms.Form):
    land_line_number = PhoneNumberField()


class MobileDataForm(forms.ModelForm):

    division = forms.ModelChoiceField(queryset=Location.get_division_queryset())

    city = forms.ModelChoiceField(queryset=Location.get_city_queryset())

    thana = forms.ModelChoiceField(queryset=Location.get_thana_queryset())

    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(), required=False, widget=Select2MultipleWidget
    )

    photo1 = forms.ImageField(required=False)
    photo2 = forms.ImageField(required=False)

    class Meta:
        model = MobileNumberData
        fields = ['store_name', 'name', 'designation', 'email', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['thana'].initial = self.instance.location
            self.fields['city'].initial = self.instance.location.parent
            self.fields['division'].initial = self.instance.location.parent.parent
        except Exception as e:
            pass

    def clean(self):
        cleaned_data = super().clean()
        mobile_numbers = self.data.getlist('mobile_numbers[]')
        land_line_numbers = self.data.getlist('land_line_numbers[]')

        if not mobile_numbers:
            raise forms.ValidationError('Mobile Numbers are required')

        for land_line_number in land_line_numbers:
            n = _LandLineNumberHyperForm(data={'land_line_number':land_line_number})
        if mobile_numbers:
            for mobile_number in mobile_numbers:
                tf = _MobileNumberHelperForm(data={'mobile_number': mobile_number})
                if not tf.is_valid():
                    raise forms.ValidationError('%s is not a valid mobile number' % mobile_number)
        self.land_line_numbers = land_line_numbers
        self.mobile_numbers = mobile_numbers
        # checking the unique email value
        # if self.data.get('email'):
        #     if MobileNumberData.objects.filter(email__iexact=cleaned_data['email']).exists():
        #         raise forms.ValidationError('Email is already taken')
        #     else:
        #         pass
        # ss = [f.numbers for f in MobileNumberData.objects.all()]
        # marged_one = list(itertools.chain.from_iterable(ss))

        # checking for mobile number unique
        if mobile_numbers:
            for m in mobile_numbers:
                if m and m.strip() != '':
                    if MobileNumberData.objects.mongo_find({'numbers':m}).count() > 0:
                        raise forms.ValidationError("Mobile number %s already exists" % m)

        # for land line number unique checking
        if land_line_numbers :
            for mn in land_line_numbers:
                if mn and mn.strip() != '':
                    if MobileNumberData.objects.mongo_find({'land_line_numbers':mn}).count() > 0:
                        raise forms.ValidationError("Land Line number %s already exists" % mn)

        return cleaned_data

    def build_name(self, new_pref, old_name):
        return '%s_%s.%s' % (new_pref, time.strftime("%Y%m%d_%H%M%S"), old_name.split('.')[1])

    def save(self, commit=False):
        instance = super().save(commit=False)
        # Location
        instance.location = self.cleaned_data['thana']
        # Mobile Numbers
        instance.numbers = self.mobile_numbers
        # Land Line number
        instance.land_line_numbers = self.land_line_numbers

        # saving categories
        [instance.categories.add(cat) for cat in self.cleaned_data['categories']]

        # saving photos
        photos = []

        if self.cleaned_data['photo1']:
            p1 = UploadedImage.objects.create()
            p1.image.save(self.build_name(instance.store_name, self.cleaned_data['photo1'].name), self.cleaned_data['photo1'])
            p1.save()
            photos.append(p1)

        if self.cleaned_data['photo2']:
            p2 = UploadedImage.objects.create()
            p2.image.save(self.build_name(instance.store_name, self.cleaned_data['photo2'].name), self.cleaned_data['photo2'])
            p2.save()
            photos.append(p2)

        [instance.photos.add(photo) for photo in photos]

        instance.save()
        return instance


class MobileDataUpdateForm(forms.ModelForm):
    is_update = False
    division = forms.ModelChoiceField(queryset=Location.get_division_queryset())

    city = forms.ModelChoiceField(queryset=Location.get_city_queryset())

    thana = forms.ModelChoiceField(queryset=Location.get_thana_queryset())
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(), required=False, widget=Select2MultipleWidget
    )
    photo1 = forms.ImageField(required=False)
    photo2 = forms.ImageField(required=False)
    class Meta:
        model = MobileNumberData
        fields = ['store_name', 'name', 'designation', 'email', 'address', 'categories', 'photo1', 'photo2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['thana'].initial = self.instance.location
            self.fields['city'].initial = self.instance.location.parent
            self.fields['division'].initial = self.instance.location.parent.parent
            if(self.instance.photos.first()):
                self.fields['photo1'].initial = self.instance.photos.first().image
            if((self.instance.photos) == 2 and self.instance.photos.last()):
                self.fields['photo2'].initial = self.instance.photos.last().image
                self.is_update = True
        except Exception as e:
            pass

    def build_name(self, new_pref, old_name):
        return '%s_%s.%s' % (new_pref, time.strftime("%Y%m%d_%H%M%S"), old_name.split('.')[1])

    def clean(self):
        cleaned_data = super().clean()
        mobile_numbers = self.data.getlist('mobile_numbers[]')
        land_line_numbers = self.data.getlist('land_line_numbers[]')
        self.image1 = self.cleaned_data['photo1']
        self.image2 = self.cleaned_data['photo2']

        for land_line_number in land_line_numbers:
            n = _LandLineNumberHyperForm(data={'land_line_number':land_line_number})
        if not mobile_numbers:
            raise forms.ValidationError('Mobile Numbers are required')
        else:
            for mobile_number in mobile_numbers:
                tf = _MobileNumberHelperForm(data={'mobile_number': mobile_number})
                if not tf.is_valid():
                    raise forms.ValidationError('%s is not a valid mobile number' % mobile_number)


        self.land_line_numbers = land_line_numbers
        self.mobile_numbers = mobile_numbers

        return cleaned_data

    def save(self, commit=False):
        instance = super().save(commit=False)
        # Location
        instance.location = self.cleaned_data['thana']
        # Mobile Numbers
        instance.numbers = self.mobile_numbers
        # Land Line number
        instance.land_line_numbers = self.land_line_numbers

        if self.image1 is not None:
            if instance.photos.first() is not None:
                p1 = UploadedImage.objects.filter(_id=instance.photos.first()._id).first()
                p1.image.save(self.build_name(instance.store_name, self.image1.name), self.image1)
                p1.save()
            else:
                p1 = UploadedImage.objects.create()
                p1.image.save(self.build_name(instance.store_name, self.image1.name), self.image1)
                p1.save()

            instance.photos.add(p1)

        if self.image2 is not None:
            if self.is_update == True and  instance.photos.last() is not None:
                p2 = UploadedImage.objects.filter(_id=instance.photos.last()._id).first()
                p2.image.save(self.build_name(instance.store_name, self.image2.name), self.image2)
                p2.save()
            else:
                p2 = UploadedImage.objects.create()
                p2.image.save(self.build_name(instance.store_name, self.image2.name), self.image2)
                p2.save()

            instance.photos.add(p2)

        instance.save()
        return instance


class BusinessInfoFilter(forms.Form):

    division = forms.ModelChoiceField(queryset=Location.get_division_queryset(),widget=forms.Select(attrs={'class':'form-control'}),required=False)

    city = forms.ModelChoiceField(queryset=Location.get_city_queryset(),widget=forms.Select(attrs={'class':'form-control'}),required=False)

    thana = forms.ModelChoiceField(queryset=Location.get_thana_queryset(),widget=forms.Select(attrs={'class':'form-control'}),required=False)

    category = forms.ModelChoiceField(queryset=Category.objects.all(), widget=Select2Widget,required=False)

    class Meta:
        model = BusinessInfo
        fields = ['location']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['thana'].initial = self.instance.location
            self.fields['city'].initial = self.instance.location.parent
            self.fields['division'].initial = self.instance.location.parent.parent
            self.fields['category'].initial = self.instance.category
        except Exception as e:
            pass


class MobileDataFilter(forms.Form):

    division = forms.ModelChoiceField(queryset=Location.get_division_queryset(),widget=forms.Select(attrs={'class':'form-control'}),required=False)

    city = forms.ModelChoiceField(queryset=Location.get_city_queryset(),widget=forms.Select(attrs={'class':'form-control'}),required=False)

    thana = forms.ModelChoiceField(queryset=Location.get_thana_queryset(),widget=forms.Select(attrs={'class':'form-control'}),required=False)

    category = forms.ModelChoiceField(queryset=Category.objects.none(), required=False)
    # category = forms.ChoiceField(widget=ModelSelect2Widget(
    #     model=Category,
    #     search_fields=['name__icontains']
    # ), required=False)
    class Meta:
        model = MobileNumberData
        fields = ['location']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['thana'].initial = self.instance.location
            self.fields['city'].initial = self.instance.location.parent
            self.fields['division'].initial = self.instance.location.parent.parent
            self.fields['category'].initial = self.instance.category
        except Exception as e:
            pass

