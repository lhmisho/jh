import threading
import random
import string
from django.conf import settings
from rest_framework import serializers
from johukum.consumerapi_v1 import fields as jh_fields
from johukum import models as jh_models
from phonenumbers import PhoneNumber
from django.template.loader import render_to_string
from rest_auth.serializers import LoginSerializer as LoginSerializer
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from dit_email_addon.api import DitEmailAddon
from django.contrib.auth.models import Group
from .forms import CustomPasswordResetForm

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


class LocationSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)
    # parent = jh_fields.ObjectIDField(read_only=True)

    class Meta:
        model = jh_models.Location
        fields = '__all__'


class PageSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)
    content = serializers.SerializerMethodField()

    class Meta:
        model = jh_models.Page
        fields = '__all__'

    def get_content(self, obj):
        # return obj.content.api_render(context={'page': obj.content})
        return render_to_string('partials/hyper_editor_render.html', context={'page': obj})


class CategorySerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = jh_models.Category
        fields = '__all__'

    def get_display_name(self, obj):
        return str(obj)


class BusinessInfoSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)
    location = serializers.SerializerMethodField()
    contact = serializers.SerializerMethodField()
    hours_of_operation = serializers.SerializerMethodField()

    class Meta:
        model = jh_models.BusinessInfo
        fields = '__all__'

    def get_contact(self, obj):
        return self.get_embedded_field(obj.contact)

    def get_hours_of_operation(self, obj):
        return self.get_embedded_field(obj.hours_of_operation)

    def get_location(self, obj):
        return self.get_embedded_field(obj.location)

    def get_embedded_field(self, field):
        '''
        This method browses a embedded field or list to generate
        JSON representation
        '''
        if type(field) == list:
            embedded_list = []
            for item in field:
                embedded_dict = item.__dict__
                for key in list(embedded_dict.keys()):
                    if key.startswith('_'):
                        embedded_dict.pop(key)
                    elif isinstance(embedded_dict[key], jh_models.ContactNumber):
                        embedded_dict[key] = embedded_dict[key].to_dict()
                embedded_list.append(embedded_dict)
            return_data = embedded_list
        else:
            embedded_dict = field.__dict__
            for key in list(embedded_dict.keys()):
                if key.startswith('_'):
                    embedded_dict.pop(key)
                elif isinstance(embedded_dict[key], PhoneNumber):
                    embedded_dict[key] = str(embedded_dict[key])
                elif isinstance(embedded_dict[key], jh_models.OpenClose):
                    embedded_dict[key] = embedded_dict[key].to_dict()
                elif key == "mobile_numbers":
                    item_to_iterate = embedded_dict[key] if embedded_dict[key] is not None else []
                    embedded_dict[key] = [item.to_dict() for item in item_to_iterate]
            return_data = embedded_dict
        return return_data


class CustomAuthLoginSerializer(LoginSerializer):
    # uesrname = serializers.CharField(required=True, allow_blank=False)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = None
        user_data = jh_models.User.objects.filter(Q(username=username) | Q(email=username))
        try:
            if not user_data:
                user_data = jh_models.User.objects.filter(mobile_number=username)
        except Exception as e:
            msg = 'Unable to log in with provided credentials.'
            raise ValidationError(msg)

        del attrs['username']

        if user_data:
            userEmail = user_data.first().email
            attrs['email'] = userEmail

        return super().validate(attrs)


def send_email_async(data):
    DitEmailAddon().send_email_default(data['email'], 'ACCOUNT_VARIFICATION', data)


class ConsumerRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = jh_models.User
        fields = ('first_name', 'last_name', 'email', 'mobile_number', 'password')
        write_only_fields = ('password',)
        # read_only_fields = ('id',)

    def create(self, validated_data):
        if not validated_data['email'].strip() == '':
            unique_email = jh_models.User.objects.filter(email=validated_data['email'])
            if unique_email.count() > 0:
                raise ValidationError({'email': 'User with this email already exists.'})
        if validated_data['mobile_number']:
            unique_mobile = jh_models.User.objects.filter(mobile_number=validated_data['mobile_number'])
            if unique_mobile.count() > 0:
                raise ValidationError({'mobile': 'User with this mobile number already exists.'})

        varification_code = randomString()

        user = jh_models.User.objects.create(
            username = validated_data['email'],
            email = validated_data['email'],
            mobile_number = validated_data['mobile_number'],
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
            varification_code = varification_code,
            is_active = False
        )
        group = Group.objects.get(name=settings.USER_GROUP)
        user.set_password(validated_data['password'])
        user.save()
        data = {
            'email': validated_data['email'],
            'code': varification_code
        }
        threading.Thread(target=send_email_async, args=[data]).start()
        user.groups.add(group)
        return user


from rest_auth.serializers import PasswordResetSerializer, PasswordResetConfirmSerializer
class CustomPasswordResetSerializers(PasswordResetSerializer):
    email = serializers.EmailField()
    password_reset_form_class = CustomPasswordResetForm

class CustomPasswordResetConfirmSerializer(PasswordResetConfirmSerializer):
    pass

class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = jh_models.Review
        fields = ('added_by', 'rating', 'comment', 'business_id')


class UserInfoSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)

    class Meta:
        model = jh_models.User
        fields = ('_id', 'username', 'first_name', 'last_name', 'email')
