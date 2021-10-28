# apis/views.py
from rest_framework import generics
from rest_framework import viewsets

from testdata.models import RawTestsList, ReducedPumpTestDetails, ReducedPumpTestData
from rpidaq.models import RpiDaqTestDetails, RpiDaqData
from .serializers import RawTestSerializer, RpiDaqTestDetailsSerializer, RpiDaqDataSerializer

class ListRawTest(generics.ListCreateAPIView):
    queryset = RawTestsList.objects.all()
    paginate_by = 10  
    serializer_class = RawTestSerializer


class DetailRawTest(generics.RetrieveUpdateDestroyAPIView):
    queryset = RawTestsList.objects.all()
    serializer_class = RawTestSerializer


class RpiDaqTestDetailsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows all data to be viewed or edited.
    """
    queryset = RpiDaqTestDetails.objects.all()
    serializer_class = RpiDaqTestDetailsSerializer

class RpiDaqDataViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows all data to be viewed or edited.
    """
    queryset = RpiDaqData.objects.all().order_by('-created_at')
    paginate_by = 10  
    serializer_class = RpiDaqDataSerializer
    def get_queryset(self):
        queryset = self.queryset
        testids = self.request.query_params.get('testid', None)
        if testids is not None:
            queryset = queryset.filter(testid__id=testids)
        return queryset