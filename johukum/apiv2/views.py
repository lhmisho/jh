from datetime import datetime
import time
from rest_framework import viewsets, filters, permissions, views, exceptions
from rest_framework.response import Response
from johukum.apiv2 import serializers
from johukum import models as jh_models
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http.response import HttpResponseRedirect
from django.db.models import Q
import datetime, phonenumbers
from bson import ObjectId, regex
from johukum.apiv2 import forms as apiv2_forms
from johukum import utils
from  django.db.models import Q
from django.contrib.auth.models import Group
from django.conf import settings


class PermissionHelperMixin:

    def admin_editable_only(self):
        if self.action not in ['list', 'retrieve']:
            return [permissions.IsAdminUser()]
        else:
            return []

    def authenticated_user_editable_only(self):
        if self.action not in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        else:
            return []


def get_all_locations(location_id):
    if location_id is None:
        return jh_models.Location.objects.all()
    location = jh_models.Location.objects.get(pk=location_id)
    locations = [location]
    locations = locations + list(jh_models.Location.objects.filter(parent__in=locations))
    locations = locations + list(jh_models.Location.objects.filter(parent__in=locations))
    locations = locations + list(jh_models.Location.objects.filter(parent__in=locations))
    return locations


class CategoryModelViewSet(viewsets.ModelViewSet, PermissionHelperMixin):
    queryset = jh_models.Category.objects.filter()
    serializer_class = serializers.CategorySerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ['parent']
    search_fields = ('name', 'display_name')

    def get_permissions(self):
        return self.admin_editable_only()


class AgentSelectViewSet(viewsets.ModelViewSet, PermissionHelperMixin):

    # queryset = jh_models.User.objects.filter()
    serializer_class = serializers.UserSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ['parent']
    search_fields = ('username',)

    def get_queryset(self):
        request = self.request
        return self.request.user.get_children

    def get_permissions(self):
        return self.admin_editable_only()


class UploadedImageModelViewSet(viewsets.ModelViewSet, PermissionHelperMixin):
    queryset = jh_models.UploadedImage.objects.filter()
    serializer_class = serializers.UploadedImageSerializer

    def get_permissions(self):
        return self.authenticated_user_editable_only()


class UploadedVideoModelViewSet(viewsets.ModelViewSet, PermissionHelperMixin):
    queryset = jh_models.UploadedVideo.objects.filter()
    serializer_class = serializers.UploadedVideoSerializer

    def get_permissions(self):
        return self.authenticated_user_editable_only()


class LocationModelViewSet(viewsets.ModelViewSet, PermissionHelperMixin):
    queryset = jh_models.Location.objects.filter()
    serializer_class = serializers.LocationSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ['parent', 'location_type']
    search_fields = ('name',)

    def get_permissions(self):
        return self.admin_editable_only()


class PaymentViewSet(viewsets.ModelViewSet, PermissionHelperMixin):
    queryset = jh_models.PaymentMethod.objects.filter()
    serializer_class = serializers.PaymentMethodSerializer
    filter_backends = (filters.SearchFilter, )
    search_fields = ('name',)

    def get_permissions(self):
        return self.admin_editable_only()


class ProfessionalAssociationViewSet(viewsets.ModelViewSet, PermissionHelperMixin):
    queryset = jh_models.ProfessionalAssociation.objects.filter()
    serializer_class = serializers.ProfessionalAssociationSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)

    def get_permissions(self):
        return self.admin_editable_only()


class CertificationViewSet(viewsets.ModelViewSet, PermissionHelperMixin):
    queryset = jh_models.Certification.objects.filter()
    serializer_class = serializers.CertificationSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)

    def get_permissions(self):
        return self.admin_editable_only()


class FilterHelperMixin:

    def only_logged_in_user_data(self, queryset):

        # Do not include deleted ones
        queryset = queryset.filter(deleted_at=None)

        # Show only items that the user has permission
        if self.request.user.is_admin:
            return queryset
        elif self.request.user.is_agent:
            return queryset.filter(added_by=self.request.user)
        else:
            return queryset.filter(added_by__in=self.request.user.get_children)

    def add_created_by(self, instance):
        instance.added_by = self.request.user
        instance.save()

    def delete(self, instance):
        instance.deleted_by = self.request.user
        instance.deleted_at = datetime.datetime.now()
        instance.save()


class DataModelViewSet(viewsets.ModelViewSet, FilterHelperMixin):

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def filter_queryset(self, queryset):
        return self.only_logged_in_user_data(queryset)

    def perform_create(self, serializer):
        instance = serializer.save()
        self.add_created_by(instance)

    def perform_destroy(self, instance):
        self.delete(instance)


class MobileDataListViewSet(views.APIView):

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_filter_kwargs(self):
        filter_kwargs = {}
        location_id = self.request.GET.get('location')
        category = self.request.GET.get('keyword')
        search = self.request.GET.get('search')
        locations = get_all_locations(location_id)
        status = self.request.GET.get('status')
        store_name = self.request.GET.get('business_name')
        username = self.request.GET.get('username')
        numbers = self.request.GET.get('mobile_numbers')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        try:
            start_date = start_date.replace('"', '')
            end_date = end_date.replace('"', '')
        except Exception as e:
            pass

        if len(locations) > 0:
            filter_kwargs['location_id'] = {'$in': [item._id for item in locations]}

        if category:
            filter_kwargs['categories_id'] = ObjectId(category)

        if status:
            filter_kwargs['status'] = int(status)

        if store_name:
            filter_kwargs['store_name'] = {'$regex': store_name, '$options' : 'i'}

        if username:
            filter_kwargs['added_by_id'] = ObjectId(username)

        if numbers:
            filter_kwargs['numbers'] = {'$regex': numbers}

        if start_date and end_date:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            filter_kwargs['created_at'] = {
                '$gte': datetime.datetime.combine(start_date_obj, datetime.datetime.min.time()),
                '$lt': datetime.datetime.combine(end_date_obj, datetime.datetime.max.time())
            }


        if self.request.user.is_agent:
            filter_kwargs['added_by_id'] = self.request.user._id
        elif self.request.user.is_gco:
            filter_kwargs['added_by_id'] = {'$in': [item._id for item in self.request.user.get_children]}
        elif self.request.user.is_moderator:
            filter_kwargs['added_by_id'] = {'$in': [item._id for item in self.request.user.get_children]}
        filter_kwargs['deleted_at'] = None
        return filter_kwargs

    def get_projection(self):
        return {
            'name':1,
            'store_name': 1,
            'location': 1,
            'status': 1,
            'created_at': 1,
            'modified_at': 1,
            'added_by_id': 1,
            'edit_by_id' : 1
        }

    def get_queryset(self):

        queryset = jh_models.MobileNumberData.objects.mongo_find(
            self.get_filter_kwargs(),
            self.get_projection()
        )
        return queryset

    def get_count(self):
        return self.get_queryset().count()

    def get_ordering(self, queryset):
        return queryset.sort('modified_at', -1)

    def get_pagination(self, queryset):
        self.page = int(self.request.GET.get('page', 1))
        self.per_page = int(self.request.GET.get('per_page', 20))
        skip = self.per_page * (self.page - 1)
        return queryset.skip(skip).limit(20)

    def process(self, result):
        for i, _ in enumerate(result):
            result[i]['added_by'] = {}
            result[i]['edit_by']  = {}
            try:
                user = jh_models.User.objects.get(pk=result[i]['added_by_id'])
                result[i]['added_by'] = {
                    '_id': user.pk,
                    'username': user.username
                }
            except Exception as e:
                pass

            try:
                edit_user = jh_models.User.objects.get(pk=result[i]['edit_by_id'])
                result[i]['edit_by'] = {
                    '_id': edit_user.pk,
                    'username': edit_user.username
                }
            except Exception as e:
                pass
        return result

    def get(self, request, format=None):
        self.request = request
        queryset = self.get_queryset()
        queryset = self.get_ordering(queryset)
        queryset = self.get_pagination(queryset)

        return Response({
            'total': self.get_count(),
            'page': self.page,
            'per_page': self.per_page,
            'results': self.process(list(queryset))
        })


class MobileNumberDataViewSet(viewsets.ModelViewSet, FilterHelperMixin):
    # queryset = jh_models.MobileNumberData.objects.filter(deleted_at=None)
    serializer_class = serializers.MobileNumberDataSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name', 'store_name', 'numbers')
    order_fields = ('modified_at',)
    ordering = ('-modified_at',)

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        instance = serializer.save()
        self.add_created_by(instance)

    def perform_destroy(self, instance):
        self.delete(instance)

    def get_queryset(self):
        queryset = jh_models.MobileNumberData.objects.filter(deleted_at=None)
        queryset = self.only_logged_in_user_data(queryset)

        # Filtering
        location_id = self.request.GET.get('location')
        status = self.request.GET.get('status')

        if status:
            status = int(status)
            query = Q(status=status)
            queryset = queryset.filter(query)

        if location_id:
            locations = get_all_locations(location_id)
            print(locations)
            if len(locations) > 0:
                queryset = queryset.filter(location__in=locations)
        return queryset


class BusinessInfoRetrieveView(views.APIView):

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get(self, request, **kwargs):
        pk = kwargs.pop('pk')
        obj = get_object_or_404(jh_models.BusinessInfo, pk=pk)
        data = serializers.BusinessInfoSerializer(instance=obj).data
        return Response(data)


class BusinessInfoListViewSet(views.APIView):

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_filter_kwargs(self):
        filter_kwargs = {}
        location_id = self.request.GET.get('location')
        keyword = self.request.GET.get('keyword')
        search = self.request.GET.get('search')
        locations = get_all_locations(location_id)
        status = self.request.GET.get('status')
        business_name = self.request.GET.get('business_name')
        username = self.request.GET.get('username')
        mobile_numbers = self.request.GET.get('mobile_numbers')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        area = self.request.GET.get('area')

        try:
            start_date = start_date.replace('"', '')
            end_date = end_date.replace('"', '')
        except Exception as e:
            pass

        if len(locations) > 0:
            filter_kwargs['location.location_id'] = {'$in': [item._id for item in locations]}

        if keyword:
            filter_kwargs['keywords_id'] = ObjectId(keyword)

        if status:
            filter_kwargs['status'] = int(status)

        if business_name:
            filter_kwargs['location.business_name'] = {'$regex': business_name, '$options' : 'i'}

        if username:
            filter_kwargs['added_by_id'] = ObjectId(username)

        if mobile_numbers:
            # filter_kwargs['contact.mobile_numbers.mobile_number'] = {'$regex': mobile_numbers}
            filter_kwargs['contact.mobile_numbers'] = {'$elemMatch':{'mobile_number':{'$regex':mobile_numbers}}}

        if area:
            filter_kwargs['location.area'] = {'$regex': area, '$options': 'i'}

        if start_date and end_date:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S.%fZ')
            start_date_obj = start_date_obj + datetime.timedelta(days=1)
            filter_kwargs['modified_at'] = {
                '$gte': datetime.datetime.combine(start_date_obj, datetime.datetime.min.time()),
                '$lt': datetime.datetime.combine(end_date_obj, datetime.datetime.max.time())
            }

        if self.request.user.is_agent:
            filter_kwargs['added_by_id'] = self.request.user._id
        elif self.request.user.is_gco or self.request.user.is_moderator:
            filter_kwargs['added_by_id'] = {'$in': [item._id for item in self.request.user.get_children]}

        filter_kwargs['deleted_at'] = None

        return filter_kwargs

    def get_projection(self):
        return {
            'location': 1,
            'status': 1,
            'created_at': 1,
            'modified_at': 1,
            'added_by_id': 1,
            'edit_by_id': 1
        }

    def get_queryset(self):

        queryset = jh_models.BusinessInfo.objects.mongo_find(
            self.get_filter_kwargs(),
            self.get_projection()
        )
        return queryset

    def get_count(self):
        return self.get_queryset().count()

    def get_ordering(self, queryset):
        return queryset.sort('modified_at', -1)

    def get_pagination(self, queryset):
        self.page = int(self.request.GET.get('page', 1))
        self.per_page = int(self.request.GET.get('per_page', 20))
        skip = self.per_page * (self.page - 1)
        return queryset.skip(skip).limit(20)

    def process(self, result):
        for i, _ in enumerate(result):
            result[i]['added_by'] = {}
            result[i]['edit_by'] = {}
            try:
                user = jh_models.User.objects.get(pk=result[i]['added_by_id'])
                result[i]['added_by'] = {
                    '_id': user.pk,
                    'username': user.username
                }
            except Exception as e:
                pass

            try:
                edit_user = jh_models.User.objects.get(pk=result[i]['edit_by_id'])
                result[i]['edit_by'] = {
                    '_id': edit_user.pk,
                    'username': edit_user.username
                }
            except Exception as e:
                pass
        return result

    def get(self, request, format=None):
        self.request = request
        queryset = self.get_queryset()
        queryset = self.get_ordering(queryset)
        queryset = self.get_pagination(queryset)

        return Response({
            'total': self.get_count(),
            'page': self.page,
            'per_page': self.per_page,
            'results': self.process(list(queryset))
        })


class MobileNumberDataCreateView(views.APIView):

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def clean(self, data):
        mobile_numbers = data.get('numbers')
        land_line_numbers = data.get('land_line_numbers')
        email = data.get('email')

        if not email:
            raise exceptions.ValidationError("Email is requird")

        if not mobile_numbers:
            raise exceptions.ValidationError("Mobile number is required")

        if data.get('email'):
            queryset = jh_models.MobileNumberData.objects.filter(email=email)
            if self.is_update:
                queryset = queryset.filter(~Q(pk=self.pk))
            if queryset.exists():
                raise exceptions.ValidationError({'contact': "This email is already have taken"})

        if mobile_numbers:
            for m in mobile_numbers:
                if m and m.strip() != '':
                    queryset = jh_models.MobileNumberData.objects.mongo_find({'numbers':m})
                    if self.is_update:
                        queryset = jh_models.MobileNumberData.objects.mongo_find({'numbers':m, '_id': self.pk})
                    if queryset.count():
                        raise exceptions.ValidationError("Mobile number %s already exists" % m)

        if land_line_numbers :
            for mn in land_line_numbers:
                if mn and mn.strip() != '':
                    queryset = jh_models.MobileNumberData.objects.mongo_find({'land_line_numbers': mn})
                    if self.is_update:
                        queryset = jh_models.MobileNumberData.objects.mongo_find({'land_line_numbers': mn, '_id': self.pk})
                    if queryset.count():
                        raise exceptions.ValidationError("Land Line number %s already exists" % mn)

        if data.get("photos"):
            data["photos"] = list(jh_models.UploadedImage.objects.filter(
                pk__in=[ObjectId(x) for x in data.get("photos", [])]))

        if data.get("categories"):
            data["categories"] = list(jh_models.Category.objects.filter(
                pk__in=[ObjectId(x) for x in data.get("categories", [])]))

        return data

    def save(self, data, mobile_data):

        mobile_data.name = data.get('name')
        mobile_data.designation = data.get('designation')
        mobile_data.email = data.get('email')
        mobile_data.address = data.get('address')
        mobile_data.store_name = data.get('store_name')
        if data.get('categories'):
            [mobile_data.categories.add(item) for item in data.get("categories", [])]
        mobile_data.location = data.get('thana')
        mobile_data.numbers = data.get('numbers', [])
        mobile_data.land_line_numbers = data.get('land_line_numbers', [])
        [mobile_data.photos.add(item) for item in data.get("photos", [])]
        mobile_data.save()
        return mobile_data

    def post(self, request, **kwargs):

        self.is_update = request.data.get('_id') is not None
        self.pk = request.data.get('_id')

        data = self.clean(request.data)

        if self.is_update:
            mobile_data = jh_models.MobileNumberData.objects.get(pk=self.pk)
        else:
            mobile_data = jh_models.MobileNumberData()

        mobile_data = self.save(data, mobile_data)

        if self.is_update and not request.user.is_agent:
            mobile_data.reviewed_by = request.user
        else:
            mobile_data.added_by = request.user

        mobile_data.edit_by = request.user
        mobile_data.save()

        return HttpResponseRedirect('/api/v2/mobile_number_list')


class BusinessInfoCreateView(views.APIView):

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def validate(self, data):

        if data.get('location') is None or data.get('location').get('location_id') is None:
            raise exceptions.ValidationError({'location': 'Location is required'})

        if data.get('contact') is None:
            raise exceptions.ValidationError({'contact': 'Contact is required'})
        elif data.get('contact').get('mobile_numbers'):
            for number in data['contact']['mobile_numbers']:
                if number is None or number.strip() == '':
                    raise  exceptions.ValidationError({'contact': '%s Threre are some problem with this number please put again' % number})
                if not utils.business_data_mobile_number_is_unique(number):
                    raise exceptions.ValidationError({'contact': '%s is already taken' % number})

    def clean(self, data):

        self.validate(data)

        if data.get('location', {}).get('location_id'):
            data['location']['location'] = jh_models.Location.objects.get(pk=ObjectId(data['location']['location_id']))
        else:
            raise exceptions.ValidationError({'location_id': 'location_id is required'})

        if data.get('contact', {}).get("mobile_numbers"):
            mobile_numbers = data["contact"]["mobile_numbers"]
            data["contact"]["mobile_numbers"] = [jh_models.ContactNumber(mobile_number=item) for item in mobile_numbers]

        if data.get("photos"):
            data["photos"] = list(jh_models.UploadedImage.objects.filter(
                pk__in=[ObjectId(x) for x in data.get("photos", [])]))

        if data.get("videos"):
            data["videos"] = list(jh_models.UploadedVideo.objects.filter(
                pk__in=[ObjectId(x) for x in data.get("videos", [])]))

        if data.get("professional_associations"):
            data["professional_associations"] = list(jh_models.ProfessionalAssociation.objects.filter(
                pk__in=[ObjectId(x) for x in data.get("professional_associations", [])]))

        if data.get("certifications"):
            data["certifications"] = list(jh_models.Certification.objects.filter(
                pk__in=[ObjectId(x) for x in data.get("certifications", [])]))

        if data.get("keywords"):
            data["keywords"] = list(jh_models.Category.objects.filter(
                pk__in=[ObjectId(x) for x in data.get("keywords", [])]))

        if data.get("accepted_payment_methods"):
            data["accepted_payment_methods"] = list(jh_models.PaymentMethod.objects.filter(
                pk__in=[ObjectId(x) for x in data.get("accepted_payment_methods", [])]))

        if data.get('contact').get('landline_no'):
            queryset = jh_models.BusinessInfo.objects.filter(contact={'landline_no': data['contact']['landline_no']})
            if self.is_update:
                queryset = queryset.filter(~Q(pk=self.pk))
            if queryset.exists():
                raise exceptions.ValidationError({'contact': "This Land Line Number is already have taken"})

        if data['contact'].get('fax_no'):
            queryset = jh_models.BusinessInfo.objects.filter(contact={'fax_no': data['contact']['fax_no']})
            if self.is_update:
                queryset = queryset.filter(~Q(pk=self.pk))
            if queryset.exists():
                raise exceptions.ValidationError({'contact': "This Fax Number is already have taken"})

        if data['contact'].get('email'):
            queryset = jh_models.BusinessInfo.objects.filter(contact={'email': data['contact']['email']})
            if self.is_update:
                queryset = queryset.filter(~Q(pk=self.pk))
            if queryset.exists():
                raise exceptions.ValidationError({'contact': "This email is already have taken"})

        if data['location'].get('geo'):
            if isinstance(data['location']['geo'], dict):
                if isinstance(data['location']['geo'].get('coordinates'), list):
                    if len(data['location']['geo']['coordinates']) == 0:
                        data['location']['geo'] = None
                    else:
                        coordinates = data['location']['geo']['coordinates']
                        coordinates[0] = float(coordinates[0])
                        coordinates[1] = float(coordinates[1])
                        if coordinates[0] < 60:
                            coordinates[0], coordinates[1] = coordinates[1], coordinates[0]
                        
            else:
                data['location']['geo'] = None
        return data

    def time_format(self, time, nullable=False):
        try:
            return datetime.datetime.strptime(time, '%H:%M')
        except Exception as e:
            if nullable:
                return None
            return datetime.datetime.strptime(time, '%H:%M:%S')

    def save(self, data, businessInfo):
        # Setup location data
        location_data = data.get('location', {})
        businessInfo.location = jh_models.LocationInfo(
            business_name=location_data.get('business_name'),
            building=location_data.get('building'),
            street=location_data.get('street'),
            land_mark=location_data.get('land_mark'),
            area=location_data.get('area'),
            postcode=location_data.get('postcode'),
            location=location_data.get('location'),
            plus_code=location_data.get('plus_code'),
            geo=dict(location_data.get('geo')),
        )

        # Setup Contact data
        contact_data = data.get('contact', {})
        businessInfo.contact = jh_models.ContactPersonInfo(**{
            "title": contact_data.get("title"),
            "name": contact_data.get("name"),
            "designation": contact_data.get("designation"),
            "email": contact_data.get("email"),
            "mobile_numbers": contact_data.get("mobile_numbers", []),
            "landline_no": contact_data.get("landline_no"),
            "fax_no": contact_data.get("fax_no"),
            "website": contact_data.get("website"),
            "social_link": contact_data.get("social_link")
        })

        # Process Hours of operation data
        days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        hop_data = {
            "display_hours_of_operation": data.get("hours_of_operation", {}).get("display_hours_of_operation")
        }
        for day in days:
            hop_data[day] = jh_models.OpenClose(
                open_from=self.time_format(
                    data.get("hours_of_operation", {}).get(day, {}).get('open_from')),
                open_till=self.time_format(
                    data.get("hours_of_operation", {}).get(day, {}).get('open_till')),
                leisure_start=self.time_format(
                    data.get("hours_of_operation", {}).get(day, {}).get('leisure_start'), nullable=True),
                leisure_end=self.time_format(
                    data.get("hours_of_operation", {}).get(day, {}).get('leisure_end'), nullable=True),
                open_24h=data.get("hours_of_operation", {}).get(day, {}).get('open_24h', False),
                close=data.get("hours_of_operation", {}).get(day, {}).get('close', False),
            )
        businessInfo.hours_of_operation = jh_models.HoursOfOperation(**hop_data)

        businessInfo.description = data.get('description')

        businessInfo.annual_turnover = data.get('annual_turnover')

        businessInfo.no_of_employees = data.get('no_of_employees')

        businessInfo.year_of_establishment = data.get('year_of_establishment')

        businessInfo.embed_video = data.get('embed_video')

        businessInfo.save()

        # Add other data

        if self.is_update:
            businessInfo.certifications.clear()
            businessInfo.accepted_payment_methods.clear()
            businessInfo.professional_associations.clear()
            businessInfo.keywords.clear()

        [businessInfo.photos.add(item) for item in data.get("photos", [])]

        [businessInfo.videos.add(item) for item in data.get("videos", [])]

        [businessInfo.certifications.add(item) for item in data.get("certifications", [])]

        [businessInfo.accepted_payment_methods.add(item) for item in data.get("accepted_payment_methods", [])]

        [businessInfo.professional_associations.add(item) for item in data.get("professional_associations", [])]

        [businessInfo.keywords.add(item) for item in data.get("keywords", [])]

        businessInfo.save()

        return businessInfo

    def post(self, request, **kwargs):

        self.is_update = request.data.get('_id') is not None
        self.pk = request.data.get('_id')

        data = self.clean(request.data)

        if self.is_update:
            businessInfo = jh_models.BusinessInfo.objects.get(pk=self.pk)
        else:
            businessInfo = jh_models.BusinessInfo()

        businessInfo = self.save(data, businessInfo)

        if self.is_update and not request.user.is_agent:
            businessInfo.reviewed_by = request.user
        else:
            businessInfo.added_by = request.user

        # asigning BUSINESS_OWNER_GROUP if the user is business owner and if the user alreay not in business owner group
        group = Group.objects.get(name=settings.BUSINESS_OWNER_GROUP)
        if request.user.groups.filter(name=settings.USER_GROUP).exists():
            if not request.user.groups.filter(name=settings.BUSINESS_OWNER_GROUP).exists():
                request.user.groups.add(group)

        businessInfo.edit_by = request.user
        businessInfo.save()

        return HttpResponseRedirect('/api/v2/business_data/%s/' % businessInfo._id )


class BusinessDataUploadFiles(views.APIView):

    def post(self, request, **kwargs):
        pk = kwargs.pop('pk')
        obj = get_object_or_404(jh_models.BusinessInfo, pk=pk)
        form = apiv2_forms.BusinessInfoFileUploadForm(request.data,files=request.data, instance=obj)
       
        if form.is_valid():
            form.save()
        return HttpResponseRedirect('/api/v2/business_data/%s/' % obj._id)


class MobileNumberVerifyView(views.APIView):

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get(self, request):
        mobile_number = request.GET.get('mobile_number')
        unique_for = request.GET.get('unique_for', 'business_data')
        resp = {
            'valid': False
        }
        form = apiv2_forms.MobileNumberValidationForm(data={
            'mobile_number': mobile_number
        })
        if form.is_valid():
            is_unique = True
            if unique_for == 'business_data':
                is_unique = utils.business_data_mobile_number_is_unique(mobile_number)

            if is_unique:
                return Response({'valid': True})
            else:
                return Response({'valid': False, 'message': '%s is already taken' % mobile_number})
        else:
            return Response({'valid': False, 'message': '%s is not a valid mobile number' % mobile_number})


class DashboardViewSet(views.APIView):
    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get(self, request, **kwargs):
        # pk = kwargs.pop('pk')
        # obj = get_object_or_404(jh_models.BusinessInfo, pk=pk)
        # data = serializers.BusinessInfoSerializer(instance=obj).data
        # return Response(data)

        analytics = {}
        if request.user.is_admin:
            analytics['total_agents'] = Group.objects.filter(name=settings.AGENT_GROUP).first().user_set.count()
            analytics['total_gcos'] = Group.objects.filter(name=settings.GCO_GROUP).first().user_set.count()
            analytics['total_moderators'] = Group.objects.filter(name=settings.MODERATOR_GROUP).first().user_set.count()
            analytics['total_editors'] = Group.objects.filter(name=settings.EDITOR_GROUP).first().user_set.count()
            analytics['total_business_data'] = jh_models.BusinessInfo.objects.all().count()
            analytics['total_pending_business_data'] = jh_models.BusinessInfo.objects.filter(status=1).count()
            analytics['total_rejected_business_data'] = jh_models.BusinessInfo.objects.filter(status=0).count()
            analytics['total_approved_business_data'] = jh_models.BusinessInfo.objects.filter(status=3).count()
            analytics['totoal_mobile_data'] = jh_models.MobileNumberData.objects.all().count()

        elif request.user.is_agent:
            analytics['total_added'] = jh_models.BusinessInfo.objects.filter(added_by=request.user,
                                                                          deleted_at=None).count()
            analytics['total_pending'] = jh_models.BusinessInfo.objects.filter(added_by=request.user,
                                                                            status=jh_models.BusinessInfo.PENDING,
                                                                            deleted_at=None).count()
            analytics['total_approved'] = jh_models.BusinessInfo.objects.filter(added_by=request.user,
                                                                             status=jh_models.BusinessInfo.APPROVED,
                                                                             deleted_at=None).count()
            analytics['total_reviewed'] = jh_models.BusinessInfo.objects.filter(added_by=request.user,
                                                                             status=jh_models.BusinessInfo.REVIEWED,
                                                                             deleted_at=None).count()
            analytics['total_rejected'] = jh_models.BusinessInfo.objects.filter(added_by=request.user,
                                                                             status=jh_models.BusinessInfo.REJECTED,
                                                                             deleted_at=None).count()
            analytics['total_business_data'] = jh_models.BusinessInfo.objects.filter(added_by=request.user,
                                                                                  deleted_at=None).count()
            analytics['totoal_mobile_data'] = jh_models.MobileNumberData.objects.filter(added_by=request.user,
                                                                                     deleted_at=None).count()

        elif request.user.is_editor:
            analytics['total_added'] = jh_models.BusinessInfo.objects.filter(added_by=request.user,
                                                                          deleted_at=None).count()
            analytics['total_reviewed'] = jh_models.BusinessInfo.objects.filter(reviewed_by=request.user,
                                                                             status=jh_models.BusinessInfo.REVIEWED,
                                                                             deleted_at=None).count()
            analytics['total_approved'] = jh_models.BusinessInfo.objects.filter(approved_by=request.user,
                                                                             status=jh_models.BusinessInfo.APPROVED,
                                                                             deleted_at=None).count()
            analytics['total_rejected'] = jh_models.BusinessInfo.objects.filter(rejected_by=request.user,
                                                                             status=jh_models.BusinessInfo.REJECTED,
                                                                             deleted_at=None).count()
            analytics['totoal_mobile_data'] = jh_models.MobileNumberData.objects.filter(added_by=request.user,
                                                                                     deleted_at=None).count()

        elif request.user.is_moderator:
            analytics['total_added'] = jh_models.BusinessInfo.objects.filter(added_by__in=request.user.get_children,
                                                                          deleted_at=None).count()
            analytics['total_reviewed'] = jh_models.BusinessInfo.objects.filter(reviewed_by=request.user,
                                                                             status=jh_models.BusinessInfo.REVIEWED,
                                                                             deleted_at=None).count()
            analytics['total_approved'] = jh_models.BusinessInfo.objects.filter(approved_by=request.user,
                                                                             status=jh_models.BusinessInfo.APPROVED,
                                                                             deleted_at=None).count()
            analytics['total_rejected'] = jh_models.BusinessInfo.objects.filter(rejected_by=request.user,
                                                                             status=jh_models.BusinessInfo.REJECTED,
                                                                             deleted_at=None).count()
            analytics['totoal_mobile_data'] = jh_models.MobileNumberData.objects.filter(
                                                                                added_by__in=request.user.get_children,
                                                                                deleted_at=None).count()
            analytics['total_pending'] = {}

        elif request.user.is_gco:
            analytics['total_added'] = jh_models.BusinessInfo.objects.filter(added_by=request.user,
                                                                          deleted_at=None).count()
            analytics['total_reviewed'] = jh_models.BusinessInfo.objects.filter(reviewed_by=request.user,
                                                                             status=jh_models.BusinessInfo.REVIEWED,
                                                                             deleted_at=None).count()
            analytics['total_rejected'] = jh_models.BusinessInfo.objects.filter(rejected_by=request.user,
                                                                             status=jh_models.BusinessInfo.REJECTED,
                                                                             deleted_at=None).count()
            analytics['totoal_mobile_data'] = jh_models.MobileNumberData.objects.filter(added_by=request.user,
                                                                                     deleted_at=None).count()

        return Response({'analytics': analytics})
