from analytics.repositories import core  as default_repo



def get_recent_users_list(repo = default_repo):
       
       return repo.get_recent_users()

def get_total_customers_count(repo = default_repo):

       return repo.get_total_customers_count()

def get_all_audit_log(repo = default_repo):

       return repo.get_audit_logs()

def record_admin_action(actor_id, actor_email, action, target_id, old_value, new_value, repo = default_repo):
       """
       Service-layer entry point for recording admin actions. 
       Services across the codebase call this - never the rep directly. 
       This keeps the write path consistent and testable

       """

       repo.log_admin_action(
              actor_id = actor_id,
              actor_email = actor_email, 
              action = action, 
              target_id = target_id, 
              old_value = old_value,
              new_value = new_value,
       )

def get_admin_action_logs_service(action_filter = None, repo = default_repo):
       """Returns admin action logs, optionally filtered by action type"""

       return repo.get_admin_action_logs(action_filter= action_filter)
