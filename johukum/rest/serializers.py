from rest_framework import serializers
from johukum import models
from johukum.rest import fields
from rest_framework.authtoken.serializers import AuthTokenSerializer


class CategorySerializer(serializers.ModelSerializer):
    _id = fields.ObjectIDField()

    class Meta:
        model = models.Category
        exclude = ['parent']


class LocationSerializer(serializers.ModelSerializer):
    _id = fields.ObjectIDField()

    class Meta:
        model = models.Location
        exclude = ['parent', 'prism_id', 'created_at', 'modified_at']


class BusinessInfoSerializer(serializers.ModelSerializer):
    _id = fields.ObjectIDField()
    hours_of_operation = fields.EmbededModelField()
    location = fields.EmbededModelField()

    class Meta:
        model = models.BusinessInfo
        exclude = []


class MongoEmbededMixin:

    def get_embeded_field(self, field):
        return_data = None
        if type(field) == list:
            embedded_list = []
            for item in field:
                embedded_dict = item.__dict__
                for key in list(embedded_dict.keys()):
                    if key.startswith('_'):
                        embedded_dict.pop(key)
                embedded_list.append(embedded_dict)
            return_data = embedded_list
        else:
            embedded_dict = field.__dict__
            for key in list(embedded_dict.keys()):
                if key.startswith('_'):
                    embedded_dict.pop(key)
            return_data = embedded_dict
        return return_data


class BusinessDataSerializer(serializers.ModelSerializer, MongoEmbededMixin):
    _id = fields.ObjectIDField()
    location = serializers.SerializerMethodField()
    hours_of_operation = serializers.SerializerMethodField()

    class Meta:
        model = models.BusinessInfo
        fields = ('__all__')

    def get_location(self, obj):
        return self.get_embeded_field(obj.location)

    def get_hours_of_operation(self, obj):
        return self.get_embeded_field(obj.hours_of_operation)



class MobileDataSerializer(serializers.ModelSerializer):
    _id = fields.ObjectIDField()

    class Meta:
        model = models.MobileNumberData
        fields = ('__all__')


class MobileDataCreateSerializer(serializers.ModelSerializer):
    _id = fields.ObjectIDField()

    class Meta:
        model = models.MobileNumberData
        fields = ['_id', 'name', 'designation', 'email', 'address', 'location', 'store_name', 'numbers',
                  'land_line_numbers', 'photos', 'categories']


class PaymentMethodSerializer(serializers.ModelSerializer):
    _id = fields.ObjectIDField()

    class Meta:
        model = models.PaymentMethod
        fields = ('__all__')


class TwoFactorSerializeer(AuthTokenSerializer):
    otp_code = serializers.CharField()
    method = serializers.IntegerField()

    def validate(self, attrs):
        super().validate(attrs)
        method = attrs.get('method')
        otp_code = attrs.get('otp_code')
        if not attrs['user'].verify_code(None, otp_code, method=method, api=True):
            raise serializers.ValidationError('invalid otp code', code='authorization')
        return attrs


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.User
        fields = ['email', 'username', 'password']