from rest_framework import viewsets, pagination, filters
from johukum.rest import serializers
from johukum import models
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class LargeResultsSetPagination(pagination.PageNumberPagination):
    page_size = 20000
    page_size_query_param = 'page_size'
    max_page_size = 20000


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Location.objects.all()
    serializer_class = serializers.LocationSerializer
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_fields = ('name', 'parent', 'location_type',)
    pagination_class = LargeResultsSetPagination
    ordering_fields=('name',)
    ordering=('name',)