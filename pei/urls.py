from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import PeiCalcuatorView, calculatePei, CirculatorPeiTestListView, CirculatorPeiTest2View, CirculatorPeiTest3View, circPeiPointsToTest, circPeiData

urlpatterns = [
    path(
        "peicalculator",
        login_required(PeiCalcuatorView.as_view()),
        name="peicalculator",
    ),
    path(
        "peiwizard",
        login_required(CirculatorPeiTestListView.as_view()),
        name="peiwizard",
    ),
    path(
        "peiwizard2",
        login_required(CirculatorPeiTest2View.as_view()),
        name="peiwizard2",
    ),
    path(
        "peiwizard3",
        login_required(CirculatorPeiTest3View.as_view()),
        name="peiwizard3",
    ),
    path(
        "getcircpei",
        login_required(calculatePei),
        name="getcircpei",
    ),
    path(
        "circpeipointstotest",
        login_required(circPeiPointsToTest),
        name="circpeipointstotest",
    ),
    path(
        "circpeidata",
        login_required(circPeiData),
        name="circpeidata",
    ),
]
