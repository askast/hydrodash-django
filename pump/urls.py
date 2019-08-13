from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import PumpListView, createSubmittalCurves

urlpatterns = [
    path("pumplistview", login_required(PumpListView.as_view()), name="pumplistview"),
    path(
        "submittalcurvegen",
        login_required(createSubmittalCurves),
        name="submittalcurvegen",
    ),
]
