from rest_framework import serializers
from employers.models import Employer

class EmployerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employer
        fields = '__all__'
