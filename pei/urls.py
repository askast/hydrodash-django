from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import PeiCalcuatorView, calculateCei, CirculatorCeiTestListView, CirculatorCeiTest2View, CirculatorCeiTest3View, circCeiPointsToTest, circCeiData

urlpatterns = [
    path(
        "peicalculator",
        login_required(PeiCalcuatorView.as_view()),
        name="peicalculator",
    ),
    path(
        "ceiwizard",
        login_required(CirculatorCeiTestListView.as_view()),
        name="ceiwizard",
    ),
    path(
        "ceiwizard2",
        login_required(CirculatorCeiTest2View.as_view()),
        name="ceiwizard2",
    ),
    path(
        "ceiwizard3",
        login_required(CirculatorCeiTest3View.as_view()),
        name="ceiwizard3",
    ),
    path(
        "getcirccei",
        login_required(calculateCei),
        name="getcirccei",
    ),
    path(
        "circceipointstotest",
        login_required(circCeiPointsToTest),
        name="circceipointstotest",
    ),
    path(
        "circceidata",
        login_required(circCeiData),
        name="circceidata",
    ),
]
