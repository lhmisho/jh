from johukum import models as jh_models
from rest_framework import serializers
from johukum.apiv2 import fields as jh_fields
from phonenumbers import PhoneNumber


class UserSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)

    class Meta:
        model = jh_models.User
        fields = ('_id', 'username')


class CategorySerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = jh_models.Category
        fields = '__all__'

    def get_display_name(self, obj):
        return str(obj)


class LocationSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)
    # parent = jh_fields.ObjectIDField(read_only=True)

    class Meta:
        model = jh_models.Location
        fields = '__all__'


class UploadedImageSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)
    image = serializers.ImageField()

    class Meta:
        model = jh_models.UploadedImage
        fields = '__all__'


class UploadedVideoSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)

    class Meta:
        model = jh_models.UploadedVideo
        fields = '__all__'


class PaymentMethodSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)

    class Meta:
        model = jh_models.PaymentMethod
        fields = '__all__'


class ProfessionalAssociationSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)

    class Meta:
        model = jh_models.ProfessionalAssociation
        fields = '__all__'


class CertificationSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)

    class Meta:
        model = jh_models.Certification
        fields = '__all__'


class MobileNumberDataSerializer(serializers.ModelSerializer):
    _id = jh_fields.ObjectIDField(read_only=True)
    added_by = UserSerializer(allow_null=True)

    class Meta:
        model = jh_models.MobileNumberData
        fields = '__all__'


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
