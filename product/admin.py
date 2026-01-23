from django.contrib import admin
from .models import Category, Product, ProductImages
# Register your models here.

class ProductImageInline(admin.TabularInline):
       model = ProductImages
       extra = 1

class ProductAdmin(admin.ModelAdmin):
       inlines = [ProductImageInline]
       list_display = ('name', 'price', 'stock', 'category', 'is_active')
       list_filter = ('category', 'is_active')
       search_fields = ('name', 'description')

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)