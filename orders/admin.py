from django.contrib import admin
from .models import Order, OrderItem

# This class customizes how the list looks
class OrderAdmin(admin.ModelAdmin):
    # Show these columns in the list
    list_display = ['id', 'user', 'status', 'total_price', 'created_at']
    # Add filters on the right side
    list_filter = ['status', 'created_at']
    # Allow searching by user email or order ID
    search_fields = ['user__email', 'order_id']
    # Show the "Total Price" as read-only if you want, or editable
    readonly_fields = ['order_id'] 

# Register them!
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)