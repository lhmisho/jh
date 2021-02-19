"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.conf import settings
from johukum.views import login_with_id
from filemanager import views as file_views
from compat import url


urlpatterns = [
    path('', include('johukum.urls')),
    path('admin/', admin.site.urls),
    re_path('hijack/(?P<user_id>[\w]+)/$', login_with_id),
    path('hijack/', include('hijack.urls', namespace='hijack')),
    path('hypereditor/', include('hypereditor.urls')),
    url(r'^filer/', include('filer.urls')),
    # Filemanager
    path('browse/', file_views.BrowseIframeView.as_view(), name='extensions-browse'),
    path('api/image/', file_views.ImageSearchView.as_view(), name='extensions-image-api'),
]

if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
