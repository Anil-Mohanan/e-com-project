from django.contrib.auth import get_user_model
from .models import AuditLog

User = get_user_model()

def get_recent_users():
       return list(User.objects.filter(is_staff = False).values('id','first_name','email','date_joined'))

def get_total_customers_count():
       return User.objects.filter(is_staff = False).count()

def get_audit_logs():
       return AuditLog.objects.all().order_by('-created_at')

