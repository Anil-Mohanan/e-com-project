from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum
from orders.models import Order, OrderItem
from product.models import Product
from django.contrib.auth  import get_user_model
from django.db.models.functions import TruncDate
from django.core.cache import cache
from config.utils import error_response
import logging
User = get_user_model()

logger = logging.getLogger(__name__)

class DashboardSummaryView(APIView):
       """Returns the 'Big Numbers' for Admin DashBoard. Only accessible by Staff/Admins"""

       permission_classes = [IsAdminUser]# Security : regular user cannot see this 
       
       def get(self,request):
              try:
                     stored_data = cache.get('dashboard_summary')
                     if stored_data: 
                            return Response(stored_data)
              except Exception as e:
                     logger.error(f"Error in Cache Read On DashboardSummaryView : {e}")
              
              try:
                     # Calculate the Total Revenus
                     #Only counting the Order that status is 'peding', 'shipped', 'Delivered'
                     valid_orders = Order.objects.exclude(status__in =['Cart','Cancelled'])
              
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
                     
              except Exception as e:
                     return error_response(
                            message="There is An Error occured in Calculation",status_code=500,log_message=f"DB Error Occured in Dash Board Viewset Calculation : {e}"
                     )
              try:
                     cache.set('dashboard_summary',data,900)
              except Exception as e:
                     logger.error(f"Error Occured in Cache Writing on DashboardSummaryView: {e}")
              return Response(data)
      
class SalesChartView(APIView):
       permission_classes = [IsAdminUser]

       def get(self,request):
              #Gropu by Data
              cache_key = "sales_chart_data"
              try:
                     stored_data = cache.get(cache_key)
                     if stored_data:
                            return Response(stored_data)
              except Exception as e:
                     logger.error(f"Error in Cache Reading on SalesChartView : {e}")
              try:
                     #get orders that are not cart or cancelled 
                     valid_orders = Order.objects.exclude(status__in = ['Cart','Cancelled'])
                     sale_data = (
                     valid_orders.annotate(date=TruncDate('created_at'))
                     .values('date').annotate(total= Sum('total_price'))
                     .order_by('date')
                     )
                     final_data = list(sale_data)
              except Exception as e:
                     return error_response(message="Unable to Load Sales Chart View at this moment",status_code=500,log_message=f"DB Error in SalesChartView : {e}")
              try:
                     cache.set(cache_key,final_data,1800)
              except Exception as e:
                     logger.error(f"Cache writing Error in SalesChartView :{e}")
              return Response(final_data)

class TopSellingProductsView(APIView):
       permission_classes = [IsAdminUser]

       def get(self,request):
              cache_key = 'top_selling_products'
              try:
                     stored_data = cache.get(cache_key)
                     if stored_data:
                            return Response(stored_data)
              except Exception as e:
                     logger.error(f"error on cache reading in TopSellingProductsView : {e}")
              try:
                     top_products = (
                     OrderItem.objects.values('product__name').annotate(total_sold = Sum('quantity')).order_by('-total_sold')[:5]
                     )
              
                     data_to_cache = list(top_products)
              except Exception as e:
                     return error_response(message=f"Unable to load top selling products data.",status_code=500,log_message=f"DB error in TopSellingProductsView : {e}")
              try:
                     cache.set(cache_key,data_to_cache, 1800)
              except Exception as e:
                     logger.error(f"Error occurred in Cache Writing on TopSellingProductsView: {e}")
              return Response(data_to_cache)

class UserListView(APIView):
       """Returns a list of all non-admin users."""

       permission_classes = [IsAdminUser]

       def get(self,request):
              #  want to see : ID , Name , Email, and when they joined 
              # Exlcluding the superuser/staff only looking for customer
              cache_key = "user_list"
              try:
                     
                     stored_data = cache.get(cache_key)
                     if stored_data:
                            return Response(stored_data)
              except Exception as e:
                     
                     logger.error(f"Error in cache fetching in UserListView : {e}")
              try:
                     users = User.objects.filter(is_staff = False).values('id','first_name','email', 'date_joined')
                     data_to_cache = list(users)
              except Exception as e:
                     
                     return error_response(message="Unable to Load User Details at this moment",status_code=500,log_message=f"DB Error in UserListView : {e}")
              try:
                     cache.set(cache_key,data_to_cache,1800)       
              except Exception as e:
                     
                     logger.error(f"Error occurred in Cache Writing on UserListView : {e}")
              return Response(data_to_cache)


class LowStockProductView(APIView):
       """Returns products with less than 5 items in stock."""

       permission_classes = [IsAdminUser]

       def get(self,request):
              
              cache_key = 'low_stock_product'
              try:
                     stored_data = cache.get(cache_key)
                     if stored_data:
                            return Response(stored_data)
              except Exception as e:
                     logger.error(f"Error in Cache fetching in LowStockProductView : {e}")
              try:
                     
                     low_stock_products = Product.objects.filter(
                            stock__lte = 5,
                            is_active = True
                            ).values('id','name','stock','price')
                     data_to_cache = list(low_stock_products)
              except Exception as e:
                     return error_response(message="Unable to Load the Low Stock Details at this moment",status_code=500,log_message=f"DB error in LowStockProductView : {e}")
              try:
                     
                     cache.set(cache_key,data_to_cache,1800)
              except Exception as e:
                     logger.error(f"Error occurred in Cache Writing on LowStockProductView : {e}")
              return Response(data_to_cache)