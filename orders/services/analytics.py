from .import repositories as default_repo

def get_dashboard_order_metrics(repo=default_repo):
       return repo.get_dashboard_order_metrics()

def get_daily_sales_chart_data(repo=default_repo):
       return repo.get_daily_sales_chart_data()

def get_monthly_sales_chart_data(repo=default_repo):
       return repo.get_monthly_sales_chart_data()


def get_top_selling_products(repo=default_repo):
       return repo.get_top_selling_products()