from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Product , Category
from .serializers import ProductSerializer, CategroySerializer

class ProductViewSet(viewsets.ModelViewSet):
       queryset = Product.objects.all()
       
       serializer_class  = ProductSerializer

       permission_classes =  [permissions.AllowAny] # setting the permisssion classes to Allow any for now 
       
       lookup_field = 'slug'

class CategoryViewSet(viewsets.ModelViewSet):
       queryset = Category.objects.all()
       serializer_class = CategroySerializer
       permission_classes = [permissions.AllowAny]
       
