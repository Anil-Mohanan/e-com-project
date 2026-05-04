from django.db.models import query
from django.contrib.auth import get_user_model
from analytics.models import AuditLog

User = get_user_model()

def get_recent_users():
       return list(User.objects.filter(is_staff = False).values('id','first_name','email','date_joined'))

def get_total_customers_count():
       return User.objects.filter(is_staff = False).count()

def get_audit_logs():
       return AuditLog.objects.all().order_by('-created_at')

def log_admin_action(actor_id, actor_email, action, target_id, old_value, new_value):
       """
       Writes one row to AdminActionLog.
       Called by service function whene ever an admin performs a cirtical action.
       Never called from views directily - alwasy goes throguh the service layer.

       """
       from analytics.models import AdminActionLog

       AdminActionLog.objects.create(
              actor_id = actor_id,
              actor_email = actor_email,
              action = action,
              target_id = str(target_id),# str() becuase target_id might be a UUID - Normalize to string
              old_value = old_value,
              new_value = new_value,
       )

def get_admin_action_logs(action_filter = None, limit = 100):
       """
       Returns recent admin action logs , optionally filtered by action type. 
       Used by the admin dashboard to review who chaged what.

       """
       from analytics.models import AdminActionLog

       queryset = AdminActionLog.objects.all()
       #all() returns the full queryset ordering= '-timestamp' applies from Meta

       if action_filter:
              queryset = queryset.filter(action = action_filter)
              # Admin can filter : ? action = order.status_changed

       return queryset[:limit]
