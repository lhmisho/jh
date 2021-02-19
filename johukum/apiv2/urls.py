from django.urls import path, include
from rest_framework import routers
from johukum.apiv2 import views as jh_views
from django.views.decorators.csrf import csrf_exempt

router = routers.SimpleRouter()
router.register('categories', jh_views.CategoryModelViewSet)
router.register('agent/names', jh_views.AgentSelectViewSet, basename='agent_names')
router.register('locations', jh_views.LocationModelViewSet)
router.register('upload/images', jh_views.UploadedImageModelViewSet)
router.register('upload/videos', jh_views.UploadedVideoModelViewSet)
router.register('payment_methods', jh_views.PaymentViewSet)
router.register('certifications', jh_views.CertificationViewSet)
router.register('professional_associations', jh_views.ProfessionalAssociationViewSet)
router.register('mobile_number_data', jh_views.MobileNumberDataViewSet, basename='mobile_data')
# router.register('mobile_number_data_test', jh_views.MobileDataListViewSet, basename='mobile_data_test')

urlpatterns = [
    path('', include(router.urls)),
    path('business_data/', jh_views.BusinessInfoListViewSet.as_view()),
    path('business_data/create/', jh_views.BusinessInfoCreateView.as_view()),
    path('business_data/<str:pk>/', jh_views.BusinessInfoRetrieveView.as_view()),
    path('business_data/upload/<str:pk>/', jh_views.BusinessDataUploadFiles.as_view()),
    path('mobile_data/create/', jh_views.MobileNumberDataCreateView.as_view()),
    path('mobile_number/verify/', jh_views.MobileNumberVerifyView.as_view()),
    path('mobile_number_list/', jh_views.MobileDataListViewSet.as_view()),
    path('dashboard-data/', jh_views.DashboardViewSet.as_view()),
]