from django.urls import path, include, re_path
from johukum.views import *
from django.conf.urls import url
from johukum.utils import AutoResponseView
from johukum.rest import viewsets, views as rest_views
from rest_framework import routers
from rest_framework.authtoken import views
from zero_auth.views import TwoFactorSettingsView
from filemanager import views as file_views

router = routers.DefaultRouter()

router.register('categories', viewsets.CategoryViewSet)
router.register('locations', viewsets.LocationViewSet)

urlpatterns = [

    path("selectFields/auto.json/", AutoResponseView.as_view(), name="django_select2-json"),

    path('', index_view, name='homepage'),

    path('api/v2/', include('johukum.apiv2.urls')),
    path('api/consumer/v1/', include('johukum.consumerapi_v1.urls')),
    path('rest-auth/', include('rest_auth.urls')),

    # 2FA REST authentication
    path('api/v1/register/', rest_views.SignupView.as_view()),
    path('api/v1/login/', rest_views.LoginView.as_view()),
    path('api/v1/verify/', rest_views.OTPLoginView.as_view()),

    path('api/v1/', include(router.urls)),
    path('api/v1/validate_phone_number', validate_phone_number, name="validate_phone_number"),
    path('api/v1/validate_land_line_number', validate_land_line_number, name="validate_land_line_number"),
    path('api/v1/mobile_data/list/', rest_views.MobileDataListApiView.as_view(), name="mobile_data_list.api"),
    path('api/v1/mobile_data/new/', rest_views.MobileDataCreateApiView.as_view(), name="mobile_data_create.api"),
    # path('api/v1/mobile_data/<int:id>/', rest_views.MobileDataListApiView.as_view(), name="mobile_data_list.api"),
    path('api/v1/business_data/list/', rest_views.BusinessInfoListApiView.as_view(), name="business_data_list.api"),
    path('api/v1/business_data/create/', rest_views.BusinessInfoCreateApiView.as_view(), name="business_data_list.api"),
    path('api/v1/payment_method/list/', rest_views.PaymentMethodListApiView.as_view(), name="payment_method_list.api"),
    re_path('api/v1/mobile_data/(?P<pk>[a-f\d]+)/$', rest_views.MobileDataDetailApiView.as_view(), name='mobile_data.detail'),


    path('dashboard/', dashboard_view, name='dashboard'),

    # Data
    #path('dashboard/data/', BusinessInfoTableView.as_view(), name='manage_data.index'),
    path('dashboard/data/', BusinessInfoListView.as_view(), name='manage_data.index'),
    path('dashboard/data/add/', BusinessInfoCreateView.as_view(), name='manage_data.create'),
    path('dashboard/data/edit/', BusinessInfoEditLegacyView.as_view(), name='manage_data.edit'),
    re_path('dashboard/data/(?P<id>[a-f\d]+)/update/', BusinessInfoEditView.as_view(), name='manage_data.update'),
    re_path(r'^dashboard/data/(?P<id>[a-f\d]+)/$', BusinessInfoView.as_view(), name='manage_data.show'),
    re_path(r'^dashboard/data/(?P<pk>[a-f\d]+)/fileupload/$', BusinessDataFileUploadView.as_view(), name='manage_data.file_upload'),
    re_path(r'^dashboard/data/delete/(?P<id>[a-f\d]+)/$', business_info_delete_view, name='manage_data.delete'),
    re_path(r'^dashboard/data/(?P<id>[a-f\d]+)/(?P<mni>[\d]+)/$', BusinessInfoVerifyMobileNumberView.as_view(), name='manage_data.verify_mobile'),
    re_path(r'^dashboard/data/varify/(?P<id>[a-f\d]+)/(?P<mni>[\d]+)/$', varify_contact, name='manage_data.verify'),


    # Mobile Data
    path('dashboard/mobile-data/', MobileNumberListView.as_view(), name='mobile_data.index'),
    re_path(r'^dashboard/mobile-data/(?P<id>[a-f\d]+)/$', MobileDataView.as_view(), name='mobile_data.show'),
    re_path(r'^dashboard/mobile-data-update/(?P<id>[a-f\d]+)/$', MobileDataUpdateView.as_view(), name='mobile_data.update'),
    re_path(r'^dashboard/mobile-data-delete/(?P<id>[a-f\d]+)/$', mobile_data_delete_view, name='mobile_data.delete'),
    path('dashboard/mobile-data/create', MobileDataCreateView.as_view(), name='mobile_data.create'),


    # Categories
    path('dashboard/categories/', CategoryListView.as_view(), name="categories.index"),
    path('dashboard/categories/create/', CategoryFormView.as_view(), name="categories.create"),
    re_path(r'^dashboard/categories/update/(?P<id>[a-f\d]+)/$',CategoryUpdateView.as_view(), name='categories.edit'),
    re_path(r'^dashboard/categories/delete/(?P<id>[a-f\d]+)/$', category_delete_view, name="categories.delete"),


    #slider
    path('dashboard/slider/create/', SliderCreateView.as_view(), name='slider.create'),
    path('dashboard/sliders/', SliderListView.as_view(), name='slider.index'),
    re_path(r'^dashboard/slider/edit/(?P<id>[a-f\d]+)/$', SliderUpdateView.as_view(), name='slider.edit'),

    # User
    re_path(r'^dashboard/users/(?P<role>[\w]+)/$', UserListView.as_view(), name="users.index"),
    re_path(r'^dashboard/users/create/(?P<role>[\w]+)/$', UserCreateView.as_view(), name="users.create"),
    re_path(r'^dashboard/users/edit/(?P<role>[\w]+)/(?P<pk>[a-f\d]+)/$', UserUpdateView.as_view(), name="users.edit"),
    re_path(r'^dashboard/users/delete/(?P<role>[\w]+)/(?P<id>[a-f\d]+)/$', user_delete_view, name="users.delete"),

    path('dashboard/profile/', MyProfileView.as_view(), name='profile'),
    path('dashboard/two-factor/', TwoFactorSettingsView.as_view(), name='two_factor_settings_view'),
    # Locations
    path('dashboard/locations/', LocationTableView.as_view(), name='locations.index'),
    path('dashboard/locations/create/', LocationCreateView.as_view(), name='locations.create'),
    re_path(r'^dashboard/locations/update/(?P<id>[a-f\d]+)/$',LocationsUpdateView.as_view(), name='locations.edit'),
    re_path(r'^dashboard/locations/delete/(?P<id>[a-f\d]+)/$', location_delete_view, name="locations.delete"),


    # Payment Methods
    path('dashboard/payment_methods/', PaymentMethodTableView.as_view(), name='payment_methods.index'),
    path('dashboard/payment_methods/create/', PaymentMethodCreateView.as_view(), name='payment_methods.create'),
    re_path(r'^dashboard/payment_methods/update/(?P<id>[a-f\d]+)/$', PaymentMethodUpdateView.as_view(), name='payment_methods.update'),
    re_path(r'^dashboard/payment_methods/delete/(?P<id>[a-f\d]+)/$', payment_delete_view, name="payment_methods.delete"),

    # Professional Association
    path('dashboard/professional_associations/', ProfessionalAssociationTableView.as_view(), name='professional_associations.index'),
    path('dashboard/professional_associations/create/', ProfessionalAssociationCreateView.as_view(), name='professional_associations.create'),
    re_path(r'^dashboard/professional_associationss/update/(?P<id>[a-f\d]+)/$', ProfessionalAssociationUpdateView.as_view(), name='professional_associations.update'),
    re_path(r'^dashboard/professional_associations/delete/(?P<id>[a-f\d]+)/$', professionalAssociation_delete_view, name="professional_associations.delete"),


    # Professional Association
    path('dashboard/certifications/', CertificationTableView.as_view(), name='certifications.index'),
    path('dashboard/certifications/create/', CertificationCreateView.as_view(), name='certifications.create'),
    re_path(r'^dashboard/certifications/update/(?P<id>[a-f\d]+)/$', CertificationUpdateView.as_view(), name='certifications.update'),
    re_path(r'^dashboard/certifications/delete/(?P<id>[a-f\d]+)/$', certification_delete_view, name="certifications.delete"),


    # Date Range Reports
    path('dashboard/reports/agent-report/', ReportView.as_view(), name='reports.index'),
    path('dashboard/reports/agent-report/mobile/', MobileReportView.as_view(), name='mobile_reports.index'),
    path('dashboard/reports/editor-report/', EditorReportView.as_view(), name='editor_reports.index'),
    path('dashboard/reports/category', CategoryReport.as_view(), name='category_report.index'),

    # Authentication
    path('accounts/login/', TwoFactorLoginView.as_view(), name='login'),
    path('accounts/', include('django.contrib.auth.urls'))


]
