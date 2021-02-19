import django_filters as filters
from johukum import models
from djongo import models as d_models
from django_select2.forms import Select2Widget

class LocationFilter(filters.FilterSet):

    name = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = models.Location
        fields = ['location_type']



class BusinessInfoFilter(filters.FilterSet):
    class Meta:
        model = models.BusinessInfo
        fields = {
            'keywords': ['in']
        }
