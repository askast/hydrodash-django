from rest_framework import serializers
from testdata.models import RawTestsList, ReducedPumpTestDetails, ReducedPumpTestData
from rpidaq.models import RpiDaqTestDetails, RpiDaqData


class RawTestSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
            'headunits_choices',
            'powerunits_choices',
            'flowunits_choices',
            'tempunits_choices',
            'headfield',
            'flowfield',
            'powerfield',
            'torquefield',
            'headunits',
            'flowunits',
            'powerunits',
            'tempunits',
            'rpmfield',
            'path',
            'testname',
            'testdate',
            'datareduced',
            'fileupload',
            'hidden',
            'testdatatype',
        )
        model = RawTestsList



class RpiDaqTestDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'testname',
            'testdate',
            'description',
        )
        model = RpiDaqTestDetails
        
class RpiDaqDataSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            'id',
            'testid',
            'created_at',
            'channel_1', 
            'channel_2', 
            'channel_3', 
            'channel_4', 
            'channel_5', 
            'channel_6', 
            'channel_7', 
            'channel_8', 
            'channel_9', 
            'channel_10',
            'channel_11',
            'channel_12',
            'channel_13',
            'channel_14',
            'channel_15',
            'channel_16',
            'channel_17',
            'channel_18',
            'channel_19',
            'channel_21',
            'channel_22',
            'channel_23',
            'channel_24',
            'channel_25',
            'channel_26',
            'channel_27',
        )
        model = RpiDaqData