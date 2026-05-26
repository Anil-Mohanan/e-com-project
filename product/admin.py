from re import search
from django.contrib import admin
from .models import Category, Product, ProductImages, ProductVariant,Color
# Register your models here.

class ProductImageInline(admin.TabularInline):
# Defines an inline interface, displaying images as a table inside the main Product admin page.
       model = ProductImages
       # Specifies that this inline is for the ProductImages model.
       fields = ['image', 'color', 'is_thumbnail', 'is_primary']
       # Explicitly lists the fields to display. Notice 'variant' is completely removed because images decouple from hardware specs.
       extra = 1
       # Django Inbuilt: Tells the admin interface to provide exactly 1 empty row for uploading a new image.

class ProductVariantInline(admin.TabularInline):
# Defines an inline interface for managing variants as a table inside the main Product admin page.
       model = ProductVariant
       # Specifies that this inline is for the ProductVariant model.
       fields = ['sku', 'color', 'attributes', 'price', 'stock', 'is_active']
       # Replaced 'attribute_name' and 'value' with the JSON 'attributes' field and the 'color' Foreign Key.
       extra = 0
       # Django Inbuilt: Tells the admin interface to provide 0 empty rows by default to keep the UI clean.

class ProductAdmin(admin.ModelAdmin):
# Defines the configuration for the main Product page in the admin panel.
       inlines = [ProductVariantInline, ProductImageInline]
       # Django Inbuilt: Embeds the variant and image tables directly inside the product creation/edit page.
       list_display = ('name', 'price', 'stock', 'category', 'is_active')
       # Django Inbuilt: Determines which columns are visible on the main list view of all products.
       list_filter = ('category', 'is_active')
       # Django Inbuilt: Adds a sidebar filter allowing the admin to filter products by category or active status.
       search_fields = ('name', 'description')
       # Django Inbuilt: Adds a search bar that queries the database using SQL LIKE clauses on the name and description columns.


admin.site.register(Category)
admin.site.register(Product, ProductAdmin) 
admin.site.register(Color)


