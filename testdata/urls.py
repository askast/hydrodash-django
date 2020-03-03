from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import TestListView, RawTestsListData, RawTestPlotView, RawTestPlotData, TestDataReduce, testDataReduceTableData, testNameValidate, reduceTestData, ReducedTestPlotView, ReducedTestListView, ReducedTestsListData, reducedTestPlotData, addSummary, DirectDataInputView

urlpatterns = [
    path('', login_required(TestListView.as_view()), name='testdata-testlist'),
    path('data', login_required(RawTestsListData.as_view()),
         name='rawtestlist-json'),
    path('plotview', login_required(RawTestPlotView.as_view()),
         name='rawtestplotview'),
    path('plotdata', login_required(RawTestPlotData),
         name='rawtestplotdata'),
    path('datareduce', login_required(TestDataReduce.as_view()),
         name='testdatareduce'),
    path('tabledata', login_required(testDataReduceTableData),
         name='datareducetabledata'),
    path('testnamevalidate', login_required(testNameValidate),
         name='testnamevalidate'),
    path('addtoreduceddatabase', login_required(reduceTestData),
         name='addtoreduceddatabase'),
    path('reducedplotview', login_required(ReducedTestPlotView.as_view()),
         name='reducedtestplotview'),
    path('reducedtestlist', login_required(
        ReducedTestListView.as_view()), name='reducedtestlist'),
    path('reducedtestlistdata', login_required(ReducedTestsListData.as_view()),
         name='reducedtestlist-json'),
    path('reducedplotdata', login_required(reducedTestPlotData),
         name='reducedtestplotdata'),
    path('addsummary', login_required(addSummary),
         name='addreducedtestdatasummary'),
    path('directdatainput', login_required(DirectDataInputView.as_view()),
         name='directdatainput'),
]
