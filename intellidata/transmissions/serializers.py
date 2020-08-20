from rest_framework import serializers
from transmissions.models import Transmission

class TransmissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transmission
        fields = '__all__'
