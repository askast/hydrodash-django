from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import (
    fudgeData,
    getPumpModels,
    getDesignIts,
    getRPMs,
    getTrims,
    addMarketingData,
    MarketingCurveListView,
    MarketingCurveListData,
    MarketingCurveView,
    marketingCurvePlotData,
    NPSHDataInput,
)

urlpatterns = [
    path("correctdata", login_required(fudgeData), name="fudgedata"),
    path("pumpmodels", login_required(getPumpModels), name="getpumpmodels"),
    path("designits", login_required(getDesignIts), name="getdesignits"),
    path("rpms", login_required(getRPMs), name="getrpms"),
    path("trims", login_required(getTrims), name="gettrims"),
    path("addmarketingdata", login_required(addMarketingData), name="addmarketingdata"),
    path(
        "marketinglistview",
        login_required(MarketingCurveListView.as_view()),
        name="marketingcurvelist",
    ),
    path(
        "marketinglist-data",
        login_required(MarketingCurveListData.as_view()),
        name="marketinglistdata",
    ),
    path(
        "marketingcurveview",
        login_required(MarketingCurveView.as_view()),
        name="marketingcurveview",
    ),
    path(
        "marketingcurve-data",
        login_required(marketingCurvePlotData),
        name="marketingcurvedata",
    ),
    path(
        "marketingnpshinput",
        login_required(NPSHDataInput.as_view()),
        name="marketingnpshinput",
    ),
]
