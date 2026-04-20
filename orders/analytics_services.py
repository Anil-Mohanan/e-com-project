from .models import Order , OrderItem
from django.db.models import Sum
from django.db.models.functions import TruncDate

def get_dashboard_order_metrics():

       valid_orders = Order.objects.valid_sales()
       total_orders = valid_orders.count()
       revenue_data = valid_orders.aggregate(Sum('total_price'))
       total_revenue  = revenue_data['total_price__sum'] or 0
       

       return {"total_orders" : total_orders,"total_revenue": total_revenue}


def get_sales_chart_data():
       valid_orders = Order.objects.valid_sales()

       sale_data = list(valid_orders.annotate(date = TruncDate('created_at')).values('date').annotate(total = Sum('total_price')).order_by('date'))

       return sale_data

def get_top_selling_products():
       # ONLY pulls top selling. Queries OrderItem. Wraps in list() instantly.
       top_products = OrderItem.objects.top_selling()
       return list(top_products)