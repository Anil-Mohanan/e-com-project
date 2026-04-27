from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from config.cache_utils import cache_response
from orders.services.analytics import get_top_selling_products
from product.services import get_low_stock_product_data
from analytics.services import get_recent_users_list,get_all_audit_log
from .serializers import AuditLogSerializer
from analytics.domain import OrderMetricsProvider, ProductMetricsProvider, UserMetricsProvider,DailyAggregationStrategy, MonthlyAggregationStrategy
import logging


logger = logging.getLogger(__name__)

class DashboardSummaryView(APIView):
       """Returns the 'Big Numbers' for Admin DashBoard. Only accessible by Staff/Admins"""

       permission_classes = [IsAdminUser]# Security : regular user cannot see this 
       
       @cache_response(key_prefix='dashboard_summary', timeout=900, error_message="There is An Error occured in Calculation")
       def get(self,request,*args, **kwargs):
              
              # 1. Register your strategies
              providers = [
                     OrderMetricsProvider(),
                     ProductMetricsProvider(),
                     UserMetricsProvider()
              ]
              
              # 2. Dynamically build the response!
              data = {}
              for provider in providers:
                     data.update(provider.get_metrics())
                     
              return Response(data)
      
class SalesChartView(APIView):
       permission_classes = [IsAdminUser]

       def get(self,request,*args, **kwargs):
              interval = request.query_params.get('interval', 'daily')
              
              # 2. Map the string to the Strategy!
              strategies = {
                     'daily': DailyAggregationStrategy(),
                     'monthly': MonthlyAggregationStrategy()
              }
              
              # Default to Daily if they pass garbage
              strategy = strategies.get(interval, DailyAggregationStrategy())
              
              # 3. Execute!
              return Response(strategy.get_data())

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
              audit_list = get_all_audit_log()
              
              serializer = self.serializer_class(audit_list, many=True)

              return Response(serializer.data)