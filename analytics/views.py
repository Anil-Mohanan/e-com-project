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

User = get_user_model()

class DashboardSummaryView(APIView):
       """Returns the 'Big Numbers' for Admin DashBoard. Only accessible by Staff/Admins"""

       permission_classes = [IsAdminUser]# Security : regular user cannot see this 
       
       def get(self,request):
              # Calculate the Total Revenus
              # Only counting the Order that status is 'peding', 'shipped', 'Delivered'
              valid_orders = Order.objects.exclude(status__in =['Cart','Cancelled'])
              
              #Aggregate sums up the 'total_price' column .Returns {'total_price__sum': 0020000};
              revenue_data = valid_orders.aggregate(Sum('total_price'))
              total_revenue = revenue_data['total_price__sum'] or 0 # Sum('total_price'), Django needs a name for the answer it gets back. By default, it combines the field name and the math function: field_name + __ + function = total_price__sum
              
              # Aggreagat : Making the calculation it the Db and rather than getting all the date to the python and doing the math one by one in python .which is slow

              total_orders = valid_orders.count()# Total Order Count
              
              total_products = Product.objects.filter(is_active = True).count()# Total Products (active ony)
              
              total_users = User.objects.filter(is_staff=False).count()#Total Customers (everyone who is not and Admin)
              
              stored_data = cache.get('dashboard_summary')

              if stored_data: 
                    return Response(stored_data)
              data = {
                     "total_revenue": total_revenue,
                     "total_orders" : total_orders,
                     "total_products": total_products,
                     "total_users": total_users  
              }
              cache.set('dashboard_summary',data,900)


              return Response(data)
      
class SalesChartView(APIView):
       permission_classes = [IsAdminUser]

       def get(self,request):
              #get orders that are not cart or cancelled 
              valid_orders = Order.objects.exclude(status__in = ['Cart','Cancelled'])
              
              #Gropu by Data
              cache_key = "sales_chart_data"
              stored_data = cache.get(cache_key)
              if stored_data:
                    
                     return Response(stored_data)
              
              sale_data = (
                     valid_orders.annotate(date=TruncDate('created_at'))
                     .values('date').annotate(total= Sum('total_price'))
                     .order_by('date')
              )
              cache.set(cache_key,list(sale_data),1800)
              return Response(sale_data)

class TopSellingProductsView(APIView):
       permission_classes = [IsAdminUser]

       def get(self,request):
              cache_key = 'top_selling_products'
              stored_data = cache.get(cache_key)
              if stored_data:
                     return Response(stored_data)
              top_products = (
                     OrderItem.objects.values('product__name').annotate(total_sold = Sum('quantity')).order_by('-total_sold')[:5]
              )
              data_to_cache = list(top_products)
              cache.set(cache_key,data_to_cache, 1800)
              return Response(data_to_cache)

class UserListView(APIView):
       """Returns a list of all non-admin users."""

       permission_classes = [IsAdminUser]

       def get(self,request):
              #  want to see : ID , Name , Email, and when they joined 
              # Exlcluding the superuser/staff only looking for customers
              
              
              cache_key = "user_list"
              stored_data = cache.get(cache_key)
              if stored_data:
                     return Response(stored_data)
              users = User.objects.filter(is_staff = False).values('id','first_name','email', 'date_joined')
              data_to_cache = list(users)
              cache.set(cache_key,data_to_cache,1800)       
              return Response(data_to_cache)


class LowStockProductView(APIView):
       """Returns products with less than 5 items in stock."""

       permission_classes = [IsAdminUser]

       def get(self,request):
              
              cache_key = 'low_stock_product'
              stored_data = cache.get(cache_key)
              if stored_data:
                     return Response(stored_data)
              low_stock_products = Product.objects.filter(
                     stock__lte = 5,
                     is_active = True
              ).values('id','name','stock','price')
              data_to_cache = list(low_stock_products)
              cache.set(cache_key,data_to_cache,1800)
              return Response(data_to_cache)