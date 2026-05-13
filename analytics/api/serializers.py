from rest_framework import serializers
from analytics.models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
       class Meta:
              model = AuditLog
              fields = '__all__'
       