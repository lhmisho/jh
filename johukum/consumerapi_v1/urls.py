from django.urls import path, include
from johukum.consumerapi_v1 import views as jh_views
from rest_framework import routers

router = routers.SimpleRouter()
router.register('locations', jh_views.LocationApiView)

urlpatterns = [
    path('', include(router.urls)),
    path('reverse_geocoding/', jh_views.ReverseGEOCodingApiView.as_view()),
    path('business_data/', jh_views.BusinessInfoListViewSet.as_view()),
    path('business_data/<str:pk>/', jh_views.BusinessInfoRetrieveView.as_view()),
    path('business_data/cat/<str:slug>/', jh_views.RetriveBusinessDataByCategory.as_view()),
    path('categories/', jh_views.CategoryApiView.as_view()),
    path('subcategories/<str:slug>/', jh_views.SubCategoryApiView.as_view()),
    # path('locations/', jh_views.LocationApiView.as_view()),
    path('pages/', jh_views.PageApiView.as_view()),
    path('report/', jh_views.ReportView.as_view()),
    path('login/', jh_views.CustomLoginView.as_view()),
    path('registration/', jh_views.ConsumerRegistrationApiView.as_view()),
    path('password-rest/', jh_views.CustomPasswordResetView.as_view()),
    path('password-rest-confirm/', jh_views.CusotomPasswordResetConfirmView.as_view()),
    path('email/verify/', jh_views.EmailVerifyView.as_view()),
    path('land_line/verify/', jh_views.LandLineVerifyView.as_view()),
    path('sliders/', jh_views.SliderApiListView.as_view()),
    path('registration/verify/', jh_views.RegistrationVerifyApi.as_view()),
    #  business owner
    path('business_owner/data/list/', jh_views.OwnerBusinessInfoList.as_view()),
    path('business/review/create/', jh_views.ConsumerReviewCreateView.as_view()),
    path('business/review/<str:pk>/', jh_views.ReviewRetrieveView.as_view()),

    # userInfo
    path('user/info/', jh_views.UserInfoApiView.as_view()),
]


