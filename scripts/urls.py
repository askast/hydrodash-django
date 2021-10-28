from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import (
    getCoeffs,
    adjust4013,
    flattenInflection,
    copyKS,
    getPEIupload,
    populatePumps,
    importOldDashboard,
    createResidentialCurves
)

urlpatterns = [
    path("", login_required(getCoeffs), name="getCoeffs"),
    path("adjust4013", login_required(adjust4013), name="adjust4013"),
    path(
        "flatteninflection", login_required(flattenInflection), name="flatteninflection"
    ),
    path("copyks", login_required(copyKS), name="copyks"),
    path("peiupload", login_required(getPEIupload), name="peiupload"),
    path("populate", login_required(populatePumps), name="populate"),
    path("import", login_required(importOldDashboard), name="import"),
    path("rescurves", login_required(createResidentialCurves), name="rescurves"),
]
