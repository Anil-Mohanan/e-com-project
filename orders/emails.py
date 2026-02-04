from django.core.mail import send_mail
from django.conf import settings
from .models import Order
from datetime import datetime

def send_order_confirmation_email(order:Order):
       """sends a confirmation email to the user after placing an order"""

       subject = f"Order Confirmed : # {str(order.order_id)[:8]}" # Showing the first 8 char
       
       message = f""" Hi {order.user.first_name}, Thank You for you're Order at EcoShop!
       
       ---------------------------------
       ORDER SUMMARY
       ---------------------------------
       
       Order ID:{order.order_id}
       Total Price: ₹{order.total_price}
       Status: {order.status}

       Items:
       {_get_item_list(order)}
       
       we will notify you when your items ship.
       
       Thanks,
       Ecoshop Team
       """
       
       email_from = settings.DEFAULT_FROM_EMAIL
       recipient_list = [order.user.email]

       send_mail(subject, message, email_from, recipient_list)

def _get_item_list(order:Order):
       """hellper to format items into a string list"""

       item_string = []
       for item in order.items.all():
              item_string.append(f"-{item.product.name} (Qty: {item.quantity})")
       return "\n".join(item_string)

def send_shipping_email(order:Order):
       """Sends and email when the admin marks the order as Shipped"""

       subject = f"Your Order has shipped! (#{str(order.order_id)[:8]})"

       message = f"""Hi {order.user.first_name},
       Your Order is on the Way
       
       We have Shipped your items to {order.shipping_address.address_line_1,{order.shipping_address.city}}

       Items:
       {_get_item_list(order)}

       Thank you for shopping with EcoShop!
       """
       email_from = settings.DEFAULT_FROM_EMAIL
       recipient_list = [order.user.email]

       send_mail(subject, message, email_from, recipient_list)

def send_cancellation_email(order:Order):
       """Sends an email the user cancel their order"""

       subject = f"Order Cancelled :# {str(order.order_id)[:8]}"

       message = f"""
       Hi {order.user.first_name},
       As requested, we have cancelled your order.
       """
       email_from = settings.DEFAULT_FROM_EMAIL
       recipient_list = [order.user.email]

       send_mail(subject,message,email_from,recipient_list)

def send_payment_success_email(order:Order):
       """Sends an email when the Payment is successfully confirmed"""

       subject = f"Payment Received for Order #{str(order.order_id)[:8]}"

       #Formating the date 
       payment_date = datetime.now().strftime("%b %d,%Y")
       try:
              method = order.payment.payment_method
       except Exception:
              method = "Cod/Online"
       message =  f"""
       Hi {order.user.first_name},
       we have sucessfully recieved your payemen of ₹{order.total_price}
       
       Your order is now being processed and will be shipped soon
       
       ------------------------------------
       PAYMENT RECEIPT
       ------------------------------------
       
       Order ID: {order.order_id}
       Amount Paid: ₹{order.total_price}
       Date: {payment_date}
       Payment Method: {method }
       -------------------------------------------
       """
       email_from = settings.DEFAULT_FROM_EMAIL
       recipient_list = [order.user.email]
       send_mail(subject, message, email_from, recipient_list)
       
