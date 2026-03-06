from django.contrib import admin
from .models import Category, Product, ProductImages, ProductVariant
# Register your models here.

class ProductImageInline(admin.TabularInline):
       model = ProductImages
       extra = 1

class ProductVariantInline(admin.TabularInline):
       model = ProductVariant
       extra = 0

class ProductAdmin(admin.ModelAdmin):
       inlines = [ProductImageInline,ProductVariantInline]
       list_display = ('name', 'price', 'stock', 'category', 'is_active')
       list_filter = ('category', 'is_active')
       search_fields = ('name', 'description')


admin.site.register(Category)
admin.site.register(Product, ProductAdmin) 