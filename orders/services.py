from .models import ShippingAddress, Order, OrderItem
from product.models import Product , ProductVariant, Category, InventoryUnit
from django.db import transaction
from .emails import send_order_confirmation_email, send_shipping_email, send_cancellation_email,send_payment_success_email
from datetime import datetime

def process_checkout(user,address_id):
       with transaction.atomic():
              #Get the cart
              order = Order.objects.current_cart(user).get()
              # Get the Address
              address = ShippingAddress.objects.get(id = address_id, user = user)
              product_ids = order.items.values_list('product_id',flat = True) # this line just grabs a list of the pure Database IDs for every product sitting in the user's cart (e.g., [15, 6, 42]).
              products = Product.objects.select_for_update().filter(id__in = product_ids).order_by('id')#.filter(id__in=product_ids) tells the database to get only the products in the cart.
              locked_products_dict = {p.id: p for p in products}
              
              items = order.items.all()
              
              for item in items:
                     product = locked_products_dict[item.product_id]
                     avalible_units = InventoryUnit.objects.select_for_update(product = product, status = 'In Stock')[:item.quantity] # why we have to use select_for_update() here and are we adding item.quality to the end of the string
                     if product.stock < item.quantity:
                            raise ValueError(f"Sorry,{product.name} is out of stock (Only {product.stock} left).")
                     for unit in avalible_units:
                            unit.status = 'Sold'
                            unit.save()
                     item.inventory_units.set(avalible_units)# what is this for 
                     product.stock -= item.quantity
                     product.save()
                     item.price_at_purchase = product.price # Saving the price now so if the changes later , the order history is correct
                     
                     item.save()
                     
              order.shipping_address = address
              order.status = 'Pending'
              order.save()
              try:
                     send_order_confirmation_email(order)
              except Exception as e:
                     print(F"Email Failed:{e}")
              

       return order

def add_to_cart_process(user,product_id,quantity):
       order, order_created = Order.objects.get_or_create_cart(user)

       item, itme_created = OrderItem.objects.get_or_create(
              order = order,
              product_id = product_id
       )
       
       if not  itme_created:
              item.quantity += quantity
       else:
              item.quantity = quantity
       item.save()
       
       order.save()
       
       return order,item
              
def update_quantity_process(user,product_id,quantity):

       order = Order.objects.current_cart(user).get()
       item = OrderItem.objects.get(order=order, product_id = product_id)
       
       if quantity < 1:     
              item.delete()
       else:
              item.quantity = quantity
              item.save()
       order.save()

       return order, item

def remove_item_process(user,product_id):
       order = Order.objects.current_cart(user).get()
       item = OrderItem.objects.get(order=order, product_id= product_id)
       item.delete()
       order.save()

       return order

def update_status_process(order,new_status):

       order.status = new_status
       order.save()
              
       if new_status == "Shipped":
              try:
                     send_shipping_email(order)
              except Exception as e:
                     print(f"Shipping email failed:{e}")
       
       return order

def cancel_order_process(order):
       
              with transaction.atomic():
                     #Resotre Stock
                     product_ids = order.items.values_list('product_id',flat = True)
                     products = Product.objects.select_for_update().filter(id__in = product_ids).order_by('id')
                     locked_products_dict = {p.id : p for p in products}
                     items = order.items.all() # items is related name in models.py OrderItem model
                     for item in items:
                            product = locked_products_dict[item.product_id]
                            product.stock += item.quantity# Add it back!
                            product.save()
                     order.status = 'Cancelled'
                     order.save()
                     try:
                            send_cancellation_email(order)
                     except Exception as e:
                            print(f"Cancellation email Failed: {e}")

              return order

def mark_as_paid_process(order):
       order.is_paid= True
       order.paid_at = datetime.now()
       
       #Trigger Eamil: Payment Success
       try:
              send_payment_success_email(order)
       except Exception as e:
              print(F"Payment email Failed:{e}")
       return order
