from rest_framework.decorators import permission_classes
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from config.cache_utils import cache_response
from orders.services.analytics import get_top_selling_products
from product.services import get_low_stock_product_data,get_cart_abandonment_report, get_zero_result_searches_service
from analytics.services import get_recent_users_list, get_all_audit_log
from .serializers import AuditLogSerializer
from analytics.domain import OrderMetricsProvider, ProductMetricsProvider, UserMetricsProvider,DailyAggregationStrategy, MonthlyAggregationStrategy
import logging


logger = logging.getLogger(__name__)

class DashboardSummaryView(APIView):
       """Returns the 'Big Numbers' for Admin DashBoard. Only accessible by Staff/Admins"""

       permission_classes = [IsAdminUser]# Security : regular user cannot see this 
       
       @cache_response(key_prefix='dashboard_summary', timeout=900, error_message="There is An Error occured in Calculation",allowed_params=['days'])
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

       @cache_response(key_prefix='top_selling_products', timeout=1800, error_message="Unable to load top selling products data.",allowed_params=[])
       def get(self,request,*args, **kwargs):
       
              top_products =  get_top_selling_products()
              data_to_cache = top_products
              return Response(data_to_cache)

class UserListView(APIView):
       """Returns a list of all non-admin users."""

       permission_classes = [IsAdminUser]

       @cache_response(key_prefix='user_list', timeout=1800, error_message="Unable to Load User Details at this moment",allowed_params=['page','search'])
       def get(self,request,*args, **kwargs):

              data_to_cache = get_recent_users_list()
              return Response(data_to_cache)


class LowStockProductView(APIView):
       """Returns products with less than 5 items in stock."""

       permission_classes = [IsAdminUser]

       @cache_response(key_prefix='low_stock_product', timeout=1800, error_message="Unable to Load the Low Stock Details at this moment",allowed_params=[])
       def get(self,request,*args, **kwargs):
              low_stock_products = get_low_stock_product_data()
              data_to_cache = low_stock_products
              return Response(data_to_cache)


class AuditLogListView(APIView):
       """Allow Admins to see a list of every single API request made to the Server"""

       permission_classes = [IsAdminUser]

       serializer_class = AuditLogSerializer
       @cache_response(key_prefix='audit_log', timeout=1800, error_message="Unable to Load the AuditLog Details at this moment",allowed_params=['page'])
       def get(self,request,*args, **kwargs):
              audit_list = get_all_audit_log()
              
              serializer = self.serializer_class(audit_list, many=True)

              return Response(serializer.data)

class CartAbandonmentReportView(APIView):
       """
       GET /api/analytics/abandonment-report/?days=30
       Reutrns products with high views but low cart additions. 
       Admin only - This is the internal business intelligence.

       """
       permission_classes = [IsAdminUser]

       def get(self,request,*args, **kwargs):
              days = min(int(request.query_params.get('days',30)),365)

              data = get_cart_abandonment_report(days = days)
              return Response(data)

class ZeroResultSearchView(APIView):
       """
       GET /api/analytics/zero-result-searches/?days=30
       Returns search queires that returned zero resutls.
       Admin only - this is catelog gap intellignece.

       """
       permission_classes = [IsAdminUser]

       def get(self,request,*args,**kwargs):
              days = int(request.query_params.get('days',30))

              data = get_zero_result_searches_service(days = days)
              return Response(data)

       
class AdminActionLogView(APIView):
       """
       GET /api/analytics/admin-actions/? action=orders.status_changed
       Returns a log of admin actions - what changed, who did it , before/after values.
       Admin only - this is internal compliance data.
       
       """
       permission_classes = [IsAdminUser]

       def get(self, request, *args, **kwargs):
              action_filter = request.query_params.get('action',None)
              #Optional filter: ?action=order.status_changed, ?action=product.price_changed
              # If not provided, returns all action types

              from analytics.services import get_admin_action_logs_service
              data = get_admin_action_logs_service(action_filter)

              return Response(list(data.values(
                     'actor_email','action', 'target_id',
                     'old_value', 'new_value', 'timestamp'
              )))