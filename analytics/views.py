from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum
from .models import AuditLog
from django.db.models.functions import TruncDate
from django.core.cache import cache
from config.cache_utils import cache_response
from config.utils import error_response
from orders.analytics_services import get_sales_chart_data, get_dashboard_order_metrics,get_top_selling_products
from product.analytics_services import get_active_products_count, get_low_stock_product_data
from .user_services import get_recent_users_list, get_total_customers_count
from .serializers import AuditLogSerializer
import logging


logger = logging.getLogger(__name__)

class DashboardSummaryView(APIView):
       """Returns the 'Big Numbers' for Admin DashBoard. Only accessible by Staff/Admins"""

       permission_classes = [IsAdminUser]# Security : regular user cannot see this 
       
       @cache_response(key_prefix='dashboard_summary', timeout=900, error_message="There is An Error occured in Calculation")
       def get(self,request,*args, **kwargs):
              
              metrics = get_dashboard_order_metrics()
              total_revenue = metrics['total_revenue']
              total_orders = metrics['total_orders']

              total_products = get_active_products_count()# Total Products (active ony)
       
              total_users = get_total_customers_count()#Total Customers (everyone who is not and Admin)
       
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
              final_data  = get_sales_chart_data()
              return Response(final_data)

class TopSellingProductsView(APIView):
       permission_classes = [IsAdminUser]

       @cache_response(key_prefix='top_selling_products', timeout=1800, error_message="Unable to load top selling products data.")
       def get(self,request,*args, **kwargs):
       
              top_products =  get_top_selling_products()
              data_to_cache = top_products
              return Response(data_to_cache)

class UserListView(APIView):
       """Returns a list of all non-admin users."""

       permission_classes = [IsAdminUser]

       @cache_response(key_prefix='user_list', timeout=1800, error_message="Unable to Load User Details at this moment")
       def get(self,request,*args, **kwargs):

              data_to_cache = get_recent_users_list()
              return Response(data_to_cache)


class LowStockProductView(APIView):
       """Returns products with less than 5 items in stock."""

       permission_classes = [IsAdminUser]

       @cache_response(key_prefix='low_stock_product', timeout=1800, error_message="Unable to Load the Low Stock Details at this moment")
       def get(self,request,*args, **kwargs):
              low_stock_products = get_low_stock_product_data()
              data_to_cache = low_stock_products
              return Response(data_to_cache)


class AuditLogListView(APIView):
       """Allow Admins to see a list of every single API request made to the Server"""

       permission_classes = [IsAdminUser]

       serializer_class = AuditLogSerializer

       def get(self,request,*args, **kwargs):
              audit_list = AuditLog.objects.all().order_by('-created_at')
              
              serializer = self.serializer_class(audit_list, many=True)

              return Response(serializer.data)