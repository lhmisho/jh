from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from zero_auth import settings
from django.conf import settings as dsettings
from bson import ObjectId
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from johukum.models import MobileNumberData, BusinessInfo, PaymentMethod, UploadedImage
from johukum.forms import UserForm
from .serializers import (MobileDataSerializer, BusinessDataSerializer, MobileDataCreateSerializer,
                          PaymentMethodSerializer, TwoFactorSerializeer)
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import parsers
import math
import datetime

AUTH_CLASSES = (SessionAuthentication, TokenAuthentication,)


class MobileDataListApiView(generics.ListAPIView):
    queryset = MobileNumberData.objects.all()
    serializer_class = MobileDataSerializer
    authentication_classes = AUTH_CLASSES
#
# class BusinessInfoListApiView(generics.ListAPIView):
#     queryset = BusinessInfo.objects.all()
#     serializer_class = BusinessDataSerializer


class UploadedImageListApiView(generics.ListCreateAPIView):
    queryset = UploadedImage.objects.all()


class MobileDataDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MobileNumberData.objects.all()
    serializer_class = MobileDataSerializer
    authentication_classes = AUTH_CLASSES


class MobileDataCreateApiView(generics.CreateAPIView):
    queryset = MobileNumberData.objects.all()
    serializer_class = MobileDataCreateSerializer
    authentication_classes = AUTH_CLASSES


class PaymentMethodListApiView(generics.ListAPIView):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    authentication_classes = AUTH_CLASSES


class SignupView(generics.GenericAPIView):

    def get_serializer_class(self):
        return None

    def post(self, request, *args, **kwargs):
        post_data = request.POST.dict()
        post_data['active'] = dsettings.SIGNUP_USER_DEFAULT_ACTIVE
        user_form = UserForm(post_data)
        if user_form.is_valid():
            user = user_form.save()
            return Response({
                'status': 'success',
                'message': 'User created successfully!',
                'id': user.pk
            })
        else:
            return Response({
                'status': 'error',
                'errors': user_form.errors
            })



class LoginView(ObtainAuthToken):

    def post(self, request, *args, **kwargs):

        if not settings.ZERO_AUTH_OTP_ENABLED:
            return super().post(request, *args, **kwargs)

        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        method = int(request.POST.get('method', user.twofactor_method))
        # send 2fa token
        user.send_code(request, method=method, api=True)
        return Response({
            'method': method,
            'otp_sent': True
        })


class OTPLoginView(ObtainAuthToken):
    serializer_class = TwoFactorSerializeer


class BusinessInfoListApiView(generics.GenericAPIView):
    authentication_classes = AUTH_CLASSES

    def process(self, item):
        # process hour of operation
        if item['hours_of_operation']['display_hours_of_operation']:
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:

                tmp_current = item['hours_of_operation'][day]
                item['hours_of_operation'][day] = {
                    "open_from": tmp_current['open_from'].strftime("%I:%M %p"),
                    "open_till": tmp_current['open_till'].strftime("%I:%M %p"),
                    "open_24h": tmp_current['open_24h'],
                    "close": tmp_current['close']
                }
        item['logo'] = self.request.build_absolute_uri(item['logo'])
        item['cover_photo'] = self.request.build_absolute_uri(item['cover_photo'])
        return item

    def get(self, request, *args, **kwargs):
        self.request = request
        perPage = int(request.GET.get('per_page', 20))
        page = int(request.GET.get('page', 1))

        skip = (page - 1) * perPage

        filter_args = {}
        count = BusinessInfo.objects.mongo_find(filter_args).count()
        result = BusinessInfo.objects.mongo_find(filter_args).skip(skip).limit(perPage)
        result = list(map(self.process, result))
        return Response({
            'total': count,
            'total_pages': math.ceil(count / perPage),
            'per_page': perPage,
            'page': page,
            'result': list(result)
        })


class BusinessInfoCreateApiView(generics.views.APIView):
    authentication_classes = AUTH_CLASSES

    def clean(self, data):

        # fix object ids
        if data.get('_id'):
            data['_id'] = ObjectId(data['_id'])
        data['location']['location_id'] = ObjectId(data['location']['location_id'])
        for key in ['keywords_id', 'accepted_payment_methods_id', 'photos_id', 'videos_id', 'professional_associations_id', 'certifications_id']:
            if data.get(key):
                data[key] = list(map(lambda x: ObjectId(x), data[key]))

        if data.get('added_by_id'):
            data['added_by_id'] = ObjectId(data['added_by_id'])

        # fix date and time
        if data['hours_of_operation']['display_hours_of_operation']:
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:
                tmp_current = data['hours_of_operation'][day]
                data['hours_of_operation'][day] = {
                    "open_from": datetime.datetime.strptime(tmp_current['open_from'], "%I:%M %p"),
                    "open_till": datetime.datetime.strptime(tmp_current['open_till'], "%I:%M %p"),
                    "open_24h": tmp_current['open_24h'],
                    "close": tmp_current['close']
                }
        # Delete Server Specific keys
        for key in ['created_at', 'modified_at', 'deleted_at', 'added_by_id']:
            if data.get(key):
                del data[key]

        # Delete file specific keys
        for key in ['cover_photo', 'logo']:
            if data.get(key):
                del data[key]

        return data

    def post(self, request, *args, **kwargs):
        request = self.request

        try:
            data = self.clean(request.data)

            data['modified_at'] = datetime.datetime.now()
            if data.get('_id'):
                obj_id = data['_id']
                del data['_id']

                BusinessInfo.objects.mongo_find_one_and_update({'_id': obj_id}, {
                    '$set': data
                })
            else:
                data['created_at'] = datetime.datetime.now()
                data['deleted_at'] = None
                data['added_by_id'] = request.user.pk
                obj_id = BusinessInfo.objects.mongo_insert(data)

        except Exception as e:
            print(e)
            raise ValidationError({ 'status': 'error', 'message': 'Invalid Data'})
        return Response({'status': 'success', 'message': 'Request success', '_id': obj_id})


