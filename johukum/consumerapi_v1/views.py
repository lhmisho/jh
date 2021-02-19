import math
import pymongo
from decimal import Decimal
from bson import ObjectId
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import views, viewsets
from johukum import models as jh_models
from johukum.consumerapi_v1 import serializers
from rest_framework import generics, filters
from django.conf import settings
from django.db.models import Q
from rest_auth.views import LoginView
from rest_auth.views import PasswordResetView
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def get_all_locations(location_id):
    if location_id is None:
        return jh_models.Location.objects.all()
    location = jh_models.Location.objects.get(pk=location_id)
    locations = [location]
    locations = locations + list(jh_models.Location.objects.filter(parent__in=locations))
    locations = locations + list(jh_models.Location.objects.filter(parent__in=locations))
    locations = locations + list(jh_models.Location.objects.filter(parent__in=locations))
    return locations


class LocationApiView(viewsets.ModelViewSet):
    queryset = jh_models.Location.objects.filter(~Q(location_type=1))
    serializer_class = serializers.LocationSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ['parent', 'location_type']
    search_fields = ('name',)


class CategoryApiView(generics.ListAPIView):
    def get_pagination(self, queryset, limit):
        self.page = int(self.request.GET.get('page', 1))
        self.per_page = int(self.request.GET.get('per_page', limit))
        skip = self.per_page * (self.page - 1)
        return queryset.skip(skip).limit(limit)

    def get_queryset(self):
        return jh_models.Category.objects.mongo_find().sort('order', 1)
        # return jh_models.Category.objects.mongo_find()

    def get(self, request, **kwargs):
        slider_data = []
        query = jh_models.Category.objects.mongo_find({})
        total = query.count()
        limit = self.request.GET.get('limit')
        if limit:
            limit = int(limit)
        else:
            limit = 11
        queryset = self.get_pagination(self.get_queryset(), limit=limit)
        slider_category_query = jh_models.Category.objects.filter(show_as_slider=True)
        for item in range(len(slider_category_query)):
            slider_data.append({
                'parent_name': slider_category_query[item].name,
                'parent_id': slider_category_query[item]._id,
                'slug': slider_category_query[item].slug,
                'results': [{'name': x.name, 'slug': x.slug, 'display_name': x.display_name, 'icon': x.icon.url if x.icon else '', 'banner': x.banner.url if x.banner else ''} for x in jh_models.Category.objects.filter(parent_id=slider_category_query[item]._id)[:10]]
            })
        category_list = list(queryset)
        category_list_processed = []

        for item in category_list:
            for field in ['banner', 'icon']:
                if item[field] is not None and item[field].strip() != '':
                    item[field] = '%s%s' % (settings.MEDIA_URL, item[field])
            category_list_processed.append(item)
        return Response({
            'total': total,
            'page': self.page,
            'per_page': self.per_page,
            'is_paginate': total > self.per_page,
            'total_page': int(total/self.per_page) + 1,
            'slider_data': list(slider_data),
            'results': category_list_processed
        })


class PageApiView(generics.ListAPIView):
    queryset = jh_models.Page.objects.filter()
    serializer_class = serializers.PageSerializer


import csv, time
class ReportView(views.APIView):

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get(self, request, **kwargs):
        # query = jh_models.Location.objects.mongo_find({'parent_id': ObjectId("5bb608df41533c632889eb8d")})
        init_q = jh_models.Location.objects.filter(parent_id="5bb608df41533c632889eb8d")

        init_data = []

        for item in range(len(init_q)):
            # import pdb;pdb.set_trace()
            aggregate_query = [
                {
                    "$unwind": "$keywords_id"
                },
                {
                    "$lookup": {
                        "from": jh_models.Category._meta.db_table,
                        "localField": "keywords_id",
                        "foreignField": "_id",
                        "as": "category"
                    }
                },
                {
                    "$match": {
                        "location.location_id": init_q[item]._id
                    }
                },
                {
                  "$group": {
                      '_id': "$keywords_id",
                      'count': {
                          '$sum': 1
                      },
                      'category': {'$addToSet': '$category'}
                  }
                }
            ]
            result_data = list(jh_models.BusinessInfo.objects.mongo_aggregate(aggregate_query))
            prepared_data = []
            for r_item in result_data:

                prepared_data.append({
                    "category_name": r_item['category'][0][0]['name'],
                    "count": r_item['count'],
                })
            init_data.append({
                'thana_id': init_q[item]._id,
                'thana_name': init_q[item].name,
                'kwargs': prepared_data
            })

        field_names = ['thana_name', 'category_name', 'count']
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="data.csv"'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for data in range(len(init_data)):
            for item in range(len(init_data[data]['kwargs'])):
                # import pdb;pdb.set_trace()
                row = writer.writerow([init_data[data]['thana_name'], init_data[data]['kwargs'][item]['category_name'], init_data[data]['kwargs'][item]['count']])

        return response


class SubCategoryApiView(views.APIView):
    def get_pagination(self, queryset):
        self.page = int(self.request.GET.get('page', 1))
        self.per_page = int(self.request.GET.get('per_page', 20))
        skip = self.per_page * (self.page - 1)
        return queryset.skip(skip).limit(20)

    def get(self, request, **kwargs):
        slug = kwargs.pop('slug')
        query = jh_models.Category.objects.get(slug=slug)
        # queryset = jh_models.Category.objects.filter(parent_id=query._id)
        queryset = jh_models.Category.objects.mongo_find({'parent_id':query._id})
        total = queryset.count()
        queryset = self.get_pagination(queryset)

        subcategory_list = list(queryset)
        subcategory_list_processed = []

        for item in subcategory_list:
            for field in ['banner', 'icon']:
                if item[field] is not None and item[field].strip() != '':
                    item[field] = '%s%s' % (settings.MEDIA_URL, item[field])
            subcategory_list_processed.append(item)

        return Response({
            'total': total,
            'page': self.page,
            'total_page': int(total/self.per_page) + 1,
            'per_page': self.per_page,
            'is_paginate': total > self.per_page,
            'parent': query.name,
            'parent_id': query._id,
            'results': subcategory_list_processed
        })


@authentication_classes([])
@permission_classes([])
class RetriveBusinessDataByCategory(views.APIView):

    def get_projection(self):
        return {
            'location': 1,
            'status': 1,
            'contact': 1,
            'created_at': 1,
            'modified_at': 1,
            'added_by_id': 1,
            'edit_by_id': 1,
            'logo': 1,
            'cover_photo': 1,
            'total_reviews': 1,
            'aggregate_rating': 1,
            'dist': 1
        }

    def build_pagination(self):
        self.page = int(self.request.GET.get('page', 1))
        self.per_page = int(self.request.GET.get('per_page', 20))
        skip = self.per_page * (self.page - 1)
        print('skip: ', skip)
        limit = 20
        pagination = {
            'edges': [
                { '$skip': skip},
                { '$limit': 20},
            ]
        }
        return skip, limit

    def get_queryset(self, filter_kewargs, lat, lon):
        filter_kwargs = filter_kewargs
        projection = self.get_projection()
        skip, limit = self.build_pagination()
        total = jh_models.BusinessInfo.objects.mongo_find(filter_kwargs, self.get_projection()).count()
        if lat and lon:
            try:
                latitude = float(lat)
                longitude = float(lon)
                if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
                    logger.error(f"Invalid lat: {latitude}, long: {longitude}")
                else:
                    queryset = jh_models.BusinessInfo.objects.mongo_aggregate([
                        {
                            '$geoNear': {
                                'near': {'type': "Point", 'coordinates': [longitude, latitude]},
                                'key': 'location.geo',
                                'distanceField': "dist.calculated",
                                'minDistance': 2,
                                'query': filter_kwargs,
                                'includeLocs': "dist.location",
                                'spherical': True
                            }
                        },
                        {'$skip': skip},
                        {'$limit': limit},
                        {'$project': projection}
                    ])
                    return  queryset, total
            except Exception as e:
                logger.error("Unable to parse lat long", e)
        else:
            queryset = jh_models.BusinessInfo.objects.mongo_find(filter_kwargs, self.get_projection())
            return queryset, total

    def get(self, request, **kwargs):
        filter_kwargs={}
        # need to filter by let and lon
        latitude = self.request.GET.get('latitude')
        longitude = self.request.GET.get('longitude')
        slug = kwargs.pop('slug')
        keyword = jh_models.Category.objects.get(slug=slug)
        filter_kwargs['keywords_id'] = ObjectId(keyword._id)
        filter_kwargs['status'] = 3
        location_id = self.request.GET.get('location')
        locations = get_all_locations(location_id)
        business_name = self.request.GET.get('business_name')

        if len(locations) > 0:
            filter_kwargs['location.location_id'] = {'$in': [item._id for item in locations]}
        if business_name:
            filter_kwargs['location.business_name'] = {'$regex': business_name, '$options' : 'i'}

        filter_kwargs['deleted_at'] = None
        filter_kwargs['location.geo'] = {'$ne': None}

        queryset, total = self.get_queryset(filter_kwargs, latitude, longitude)
        total_page = math.ceil(total / self.per_page)
        service_list = list(queryset)
        service_list_processed = []

        for item in service_list:
            for field in ['logo', 'cover_photo']:
                if item[field] is not None and item[field].strip() != '':
                    item[field] = '%s%s' % (settings.MEDIA_URL, item[field])
            service_list_processed.append(item)

        return Response({
            'total': total,
            'page': self.page,
            'total_page': total_page,
            'is_paginate': total > self.per_page,
            'per_page': self.per_page,
            'parent': keyword.name,
            'results': service_list_processed
        })


class BusinessInfoRetrieveView(views.APIView):

    def get(self, request, **kwargs):
        pk = kwargs.pop('pk')
        obj = get_object_or_404(jh_models.BusinessInfo, pk=pk)
        photos = [x.image.url for x in obj.photos.all()]
        payment_methods = [x.name for x in obj.accepted_payment_methods.all()]
        categoires = [x.name for x in obj.keywords.all()]
        pa = [x.name for x in obj.professional_associations.all()]
        certification = [x.name for x in obj.certifications.all()]
        data = serializers.BusinessInfoSerializer(instance=obj).data
        data['photo_urls'] = photos
        data['payment_methods'] = payment_methods
        data['categoires'] = categoires
        data['professional_association'] = pa
        data['certification'] = certification
        return Response(data)


@authentication_classes([])
@permission_classes([])
class BusinessInfoListViewSet(views.APIView):

    def get_filter_kwargs(self):
        filter_kwargs = {}
        location_id = self.request.GET.get('location')
        business_name = self.request.GET.get('business_name')
        keyword = self.request.GET.get('keyword')
        if location_id:
            locations = get_all_locations(location_id)
        else:
            locations = ''
        area = self.request.GET.get('area')

        if len(locations) > 0:
            filter_kwargs['location.location_id'] = {'$in': [item._id for item in locations]}

        if keyword:
            filter_kwargs['keywords_id'] = ObjectId(keyword)


        filter_kwargs['status'] = 3

        if area:
            filter_kwargs['location.area'] = {'$regex': area, '$options': 'i'}

        if business_name:
            filter_kwargs['location.business_name'] = {'$regex': business_name, '$options': 'i'}

        filter_kwargs['deleted_at'] = None
        filter_kwargs['location.geo'] = {'$ne': None}
        # latitude = self.request.GET.get('latitude')
        # longitude = self.request.GET.get('longitude')
        #
        # if latitude and longitude:
        #     try:
        #         latitude = float(latitude)
        #         longitude = float(longitude)
        #         if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
        #             logger.error(f"Invalid lat: {latitude}, long: {longitude}")
        #         else:
        #             filter_kwargs["location.geo"] = {
        #                 "$near": {
        #                     "$geometry": {
        #                         "type": "Point",
        #                         "coordinates": [longitude, latitude]
        #                     }
        #                 }
        #             }
        #     except Exception as e:
        #         logger.error("Unable to parse lat long", e)
        return filter_kwargs

    def get_projection(self):
        return {
            'location': 1,
            'contact':1,
            'status': 1,
            'created_at': 1,
            'modified_at': 1,
            'added_by_id': 1,
            'edit_by_id': 1,
            'logo': 1,
            'cover_photo': 1,
            'total_reviews': 1,
            'aggregate_rating': 1,
            'dist': 1
        }

    def build_pagination(self):
        self.page = int(self.request.GET.get('page', 1))
        self.per_page = int(self.request.GET.get('per_page', 20))
        skip = self.per_page * (self.page - 1)
        print('skip: ', skip)
        limit = 20
        pagination = {
            'edges': [
                { '$skip': skip},
                { '$limit': 20},
            ]
        }
        return skip, limit

    def get_queryset(self):
        latitude = self.request.GET.get('latitude')
        longitude = self.request.GET.get('longitude')

        filter_kwargs = self.get_filter_kwargs()
        projection = self.get_projection()
        skip, limit = self.build_pagination()
        total = jh_models.BusinessInfo.objects.mongo_find(filter_kwargs, self.get_projection()).count()
        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
                if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
                    logger.error(f"Invalid lat: {latitude}, long: {longitude}")
                else:
                    queryset = jh_models.BusinessInfo.objects.mongo_aggregate([
                        {
                            '$geoNear': {
                                'near': {'type': "Point", 'coordinates': [longitude, latitude]},
                                'key': 'location.geo',
                                'distanceField': "dist.calculated",
                                'minDistance': 2,
                                'query': filter_kwargs,
                                'includeLocs': "dist.location",
                                'spherical': True
                            }
                        },
                        {'$skip': skip},
                        {'$limit': limit},
                        {'$project': projection}
                    ])
                    return  queryset, total
            except Exception as e:
                logger.error("Unable to parse lat long", e)
        else:
            queryset = jh_models.BusinessInfo.objects.mongo_find(filter_kwargs, self.get_projection())
            return queryset, total

    def get_ordering(self, queryset):
        return queryset.sort('modified_at', -1)

    def get(self, request, format=None):
        self.request = request
        queryset, total = self.get_queryset()
        service_list = list(queryset)
        service_list_processed = []

        for item in service_list:
            for field in ['logo', 'cover_photo']:
                if item[field] is not None and item[field].strip() != '':
                    item[field] = '%s%s' % (settings.MEDIA_URL, item[field])
            service_list_processed.append(item)

        total_page = math.ceil(total / self.per_page)

        return Response({
            'total': total,
            'page': self.page,
            'total_page': total_page,
            'per_page': self.per_page,
            'is_scrollable': (int(self.request.GET.get('page', 1)) + 1) <= total_page,
            'results': service_list_processed
        })


class SliderApiListView(views.APIView):
    def get(self, request, **kwargs):
        queryset = jh_models.Slider.objects.mongo_find({})

        slider_list = list(queryset)
        slider_list_processed = []

        for item in slider_list:
            for field in ['banner',]:
                item[field] = '%s%s' % (settings.MEDIA_URL, item[field])
            slider_list_processed.append(item)

        return Response({
            'sliders': slider_list_processed
        })


class OwnerBusinessInfoList(views.APIView):

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get(self, request, **kwargs):
        user = request.user
        query = jh_models.BusinessInfo.objects.mongo_find({'added_by_id': user._id})
        return Response({'data': list(query)})


class CustomLoginView(LoginView):
    serializer_class = serializers.CustomAuthLoginSerializer


class ConsumerRegistrationApiView(generics.CreateAPIView):
    model = jh_models.User
    serializer_class = serializers.ConsumerRegistrationSerializer

    def get_permissions(self):
        return [permissions.AllowAny()]


class CustomPasswordResetView(PasswordResetView):
    model = jh_models.User
    serializer_class = serializers.CustomPasswordResetSerializers

from rest_auth.views import PasswordResetConfirmView
class CusotomPasswordResetConfirmView(PasswordResetConfirmView):
    pass

class EmailVerifyView(views.APIView):

    def get_permissions(self):
        return [permissions.AllowAny()]

    def get(self, request):
        email = request.GET.get('email')
        if not email.strip() == '':
            unique_email = jh_models.BusinessInfo.objects.filter(contact={'email': email})
            # import pdb;pdb.set_trace()
            if unique_email.count() > 0:
                return Response({'valid': False, 'message': 'User with this %s already exists.' % email})
                # raise ValidationError({'email': 'User with this %s already exists.' % email})
            else:
                return Response({'valid': True})


class LandLineVerifyView(views.APIView):

    def get_permissions(self):
        return [permissions.AllowAny()]

    def get(self, request):
        land_line = request.GET.get('land_line')
        if not land_line.strip() == '':
            land_line = jh_models.BusinessInfo.objects.filter(contact={'landline_no': land_line})
            if land_line.count() > 0:
                return Response({'valid': False, 'message': 'User with this landline  %s already exists.' % land_line})
                # raise ValidationError({'email': 'User with this %s already exists.' % email})
            else:
                return Response({'valid': True})


class RegistrationVerifyApi(views.APIView):

    def get(self, request, **kwargs):
        code = self.request.GET.get('jhcvc')
        user = jh_models.User.objects.filter(varification_code=code)
        first_user = user.first()
        first_user.is_active = True
        first_user.save()
        return Response({
            'status': 200
        })


class ConsumerReviewCreateView(views.APIView):

    def post(self, request):
        data = request.data
        business_id = data.get('business_id')
        rating = data.get('rating')
        data['added_by'] = request.user._id
        serializer = serializers.ReviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            review = jh_models.Review.objects.filter(business_id=data.get('business_id'))
            total_review = review.count()
            total_rating = Decimal(0)
            aggregate_rating = jh_models.Review.objects.filter(business_id=data.get('business_id')).values(
                'rating')
            for item in aggregate_rating:
                total_rating += Decimal(item['rating'])
            business_info = jh_models.BusinessInfo.objects.get(_id=data.get('business_id'))
            business_info.aggregate_rating = total_rating/total_review
            business_info.total_reviews = total_review
            business_info.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)


class UserInfoApiView(views.APIView):
    def get(self, request, **kwargs):
        _id = self.request.user._id
        obj = get_object_or_404(jh_models.User, pk=_id)
        data = serializers.UserInfoSerializer(instance=obj).data
        return Response(data)


class ReviewRetrieveView(views.APIView):
    def get(self, request, **kwargs):
        pk = kwargs.pop('pk')
        print(pk)
        reviews = jh_models.Review.objects.mongo_find({'business_id_id': ObjectId(pk)}).sort([("created_at", -1),])
        list_review = list(reviews)
        for item in list_review:
            user = jh_models.User.objects.get(_id=item['added_by_id'])
            item['author'] = user.first_name + ' ' + user.last_name

        return Response({
            'reviews': list_review
        })


class ReverseGEOCodingApiView(views.APIView):

    def get(self, request, **kwargs):

        try:
            latitude = float(request.GET.get('latitude'))
            longitude = float(request.GET.get('longitude'))

            filter_kwargs = {
                'the_geom': {
                    '$geoIntersects': {
                        '$geometry': {
                            'type': 'Point',
                            'coordinates': [longitude, latitude]
                        }
                    }
                }
            }
            result = list(jh_models.BangladeshMap.objects.mongo_find(filter_kwargs))
            if len(result) > 0:
                del result[0]['the_geom']
                return Response({
                    'status': 'success',
                    'data': result[0]
                })
        except Exception as e:
            logger.error('unable to reverse geocode', e)

        return Response({
            'status': 'failed'
        })