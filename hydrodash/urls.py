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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
