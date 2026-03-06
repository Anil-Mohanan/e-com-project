from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum
from .models import AuditLog
from orders.models import Order, OrderItem
from product.models import Product
from django.contrib.auth  import get_user_model
from django.db.models.functions import TruncDate
from django.core.cache import cache
from config.cache_utils import cache_response
from config.utils import error_response
from .serializers import AuditLogSerializer
import logging
User = get_user_model()

logger = logging.getLogger(__name__)

class DashboardSummaryView(APIView):
       """Returns the 'Big Numbers' for Admin DashBoard. Only accessible by Staff/Admins"""

       permission_classes = [IsAdminUser]# Security : regular user cannot see this 
       
       @cache_response(key_prefix='dashboard_summary', timeout=900, error_message="There is An Error occured in Calculation")
       def get(self,request,*args, **kwargs):
              # Calculate the Total Revenus
              #Only counting the Order that status is 'peding', 'shipped', 'Delivered'
              valid_orders = Order.objects.valid_sales()
       
              #Aggregate sums up the 'total_price' column .Returns {'total_price__sum': 0020000};
              revenue_data = valid_orders.aggregate(Sum('total_price'))
              total_revenue = revenue_data['total_price__sum'] or 0 # Sum('total_price'), Django needs a name for the answer it gets back. By default, it combines the field name and the math function: field_name + __ + function = total_price__sum
       
              # Aggreagat : Making the calculation it the Db and rather than getting all the date to the python and doing the math one by one in python .which is slow
              total_orders = valid_orders.count()# Total Order Count
       
              total_products = Product.objects.filter(is_active = True).count()# Total Products (active ony)
       
              total_users = User.objects.filter(is_staff=False).count()#Total Customers (everyone who is not and Admin)
       
              data = {
                     "total_revenue": total_revenue,
                     "total_orders" : total_orders,
                     "total_products": total_products,
                     "total_users": total_users  
              }
              return Response(data)
      
class SalesChartView(APIView):
       permission_classes = [IsAdminUser]

       @cache_response(key_prefix='sales_chart_data', timeout=1800, error_message="Unable to Load Sales Chart View at this moment")
       def get(self,request,*args, **kwargs):
              valid_orders = Order.objects.valid_sales()
              sale_data = (
                     valid_orders.annotate(date=TruncDate('created_at'))
                     .values('date').annotate(total= Sum('total_price'))
                     .order_by('date')
              )
              final_data = list(sale_data)
              return Response(final_data)

class TopSellingProductsView(APIView):
       permission_classes = [IsAdminUser]

       @cache_response(key_prefix='top_selling_products', timeout=1800, error_message="Unable to load top selling products data.")
       def get(self,request,*args, **kwargs):
              top_products = OrderItem.objects.top_selling()
              data_to_cache = list(top_products)
              return Response(data_to_cache)

class UserListView(APIView):
       """Returns a list of all non-admin users."""

       permission_classes = [IsAdminUser]

       @cache_response(key_prefix='user_list', timeout=1800, error_message="Unable to Load User Details at this moment")
       def get(self,request,*args, **kwargs):
              users = User.objects.filter(is_staff = False).values('id','first_name','email', 'date_joined')
              data_to_cache = list(users)
              return Response(data_to_cache)


class LowStockProductView(APIView):
       """Returns products with less than 5 items in stock."""

       permission_classes = [IsAdminUser]

       @cache_response(key_prefix='low_stock_product', timeout=1800, error_message="Unable to Load the Low Stock Details at this moment")
       def get(self,request,*args, **kwargs):
              low_stock_products = Product.objects.filter(
                     stock__lte = 5,
                     is_active = True
              ).values('id','name','stock','price')
              data_to_cache = list(low_stock_products)
              return Response(data_to_cache)


class AuditLogListView(APIView):
       """Allow Admins to see a list of every single API request made to the Server"""

       permission_classes = [IsAdminUser]

       serializer_class = AuditLogSerializer

       def get(self,request,*args, **kwargs):
              audit_list = AuditLog.objects.all().order_by('-created_at')
              
              serializer = self.serializer_class(audit_list, many=True)

              return Response(serializer.data)