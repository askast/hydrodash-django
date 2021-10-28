from django.urls import include, path
from rest_framework import routers

from .views import ListRawTest, DetailRawTest, RpiDaqTestDetailsViewSet, RpiDaqDataViewSet


router = routers.DefaultRouter()
router.register(r'daqtestdetails', RpiDaqTestDetailsViewSet)
router.register(r'daqdata', RpiDaqDataViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('testlist/', ListRawTest.as_view()),
    path('testlist/<int:pk>/', DetailRawTest.as_view()),

]