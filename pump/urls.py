from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import PumpListView, createSubmittalCurves, MarketingTestDataCreatorView, createRawTestData

urlpatterns = [
    path("pumplistview", login_required(PumpListView.as_view()), name="pumplistview"),
    path(
        "submittalcurvegen",
        login_required(createSubmittalCurves),
        name="submittalcurvegen",
    ),
    path(
        "marketingtestcreatorview",
        login_required(MarketingTestDataCreatorView.as_view()),
        name="marketingtestcreatorview",
    ),
    path(
        "marketingtestcreator-data",
        login_required(createRawTestData),
        name="marketingtestcreatordata",
    ),
]
