from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum
from orders.models import Order, OrderItem
from product.models import Product
from django.contrib.auth  import get_user_model
from django.db.models.functions import TruncDate

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

              return Response({
                     "total_revenue": total_revenue,
                     "total_orders" : total_orders,
                     "total_products": total_products,
                     "total_users": total_users  
              })
class SalesChartView(APIView):
       permission_classes = [IsAdminUser]

       def get(self,request):
              #get orders that are not cart or cancelled 
              valid_orders = Order.objects.exclude(status__in = ['Cart','Cancelled'])
              
              #Gropu by Data
              sale_data = (
                     valid_orders.annotate(date=TruncDate('created_at'))
                     .values('date').annotate(total= Sum('total_price'))
                     .order_by('date')
              )
              
              return Response(sale_data)

class TopSellingProductsView(APIView):
       permission_classes = [IsAdminUser]

       def get(self,reqeust):
              top_products = (
                     OrderItem.objects.values('product__name').annotate(total_sold = Sum('quantity')).order_by('-total_sold')[:5]
              )
              
              return Response(top_products)

class UserListView(APIView):
       """Returns a list of all non-admin users."""

       permission_classes = [IsAdminUser]

       def get(self,request):
              #  want to see : ID , Name , Email, and when they joined 
              # Exlcluding the superuser/staff only looking for customers
              
              users = User.objects.filter(is_staff = False).values('id','first_name','email', 'date_joined')
              return Response(users)

class LowStockProductView(APIView):
       """Returns products with less than 5 items in stock."""

       permission_classes = [IsAdminUser]

       def get(self,request):
              low_stock_products = Product.objects.filter(
                     stock__lte = 5,
                     is_active = True
              ).values('id','name','stock','price')

              return Response(low_stock_products)