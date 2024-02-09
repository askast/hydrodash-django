from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("profiles.urls")),
    path("testdata/", include("testdata.urls")),
    path("marketingdata/", include("marketingdata.urls")),
    path("pump/", include("pump.urls")),
    path("scripts/", include("scripts.urls")),
    path("pei/", include("pei.urls")),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include('apis.urls')),
    path('rpidaq/', include('rpidaq.urls')),
    path('daq/', include('daq.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
