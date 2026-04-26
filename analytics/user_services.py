from . import repositories as default_repo



def get_recent_users_list(repo = default_repo):
       
       return repo.get_recent_users()

def get_total_customers_count(repo = default_repo):

       return repo.get_total_customers_count()

def get_all_audit_log(repo = default_repo):

       return repo.get_audit_logs()

