from rest_framework import serializers
from agreements.models import Agreement

class AgreementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Agreement
        fields = '__all__'
