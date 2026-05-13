from orders.domain import NotificationStrategy,EmailNotificationStrategy
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime

def send_order_confirmation_email(email_data, strategy: NotificationStrategy = EmailNotificationStrategy()):
       
       """sends a confirmation email to the user after placing an order"""

       subject = f"Order Confirmed : # {str(email_data.order_id)[:8]}" # Showing the first 8 char
       
       message = f""" Hi {email_data.first_name}, Thank You for you're Order at EcoShop!
       
       ---------------------------------
       ORDER SUMMARY
       ---------------------------------
       
       Order ID:{email_data.order_id}
       Total Price: ₹{email_data.total_price}
       Status: {email_data.status}

       Items:
       {_get_item_list(email_data)}
       
       we will notify you when your items ship.
       
       Thanks,
       Ecoshop Team
       """

       strategy.send(subject,message,email_data.email)
       

def _get_item_list(email_data):
       """hellper to format items into a string list"""

       item_string = []
       for item in email_data.items:
              item_string.append(f"-{item.product_name} (Qty: {item.quantity})")
       return "\n".join(item_string)

def send_shipping_email(email_data, strategy: NotificationStrategy = EmailNotificationStrategy()):
       """Sends and email when the admin marks the order as Shipped"""

       subject = f"Your Order has shipped! (#{str(email_data.order_id)[:8]})"

       message = f"""Hi {email_data.first_name},
       Your Order is on the Way
       
       We have Shipped your items to {email_data.address_line_1}, {email_data.city}

       Items:
       {_get_item_list(email_data)}

       Thank you for shopping with EcoShop!
       """
       strategy.send(subject, message, email_data.email)

def send_cancellation_email(email_data, strategy: NotificationStrategy = EmailNotificationStrategy()):
       """Sends an email the user cancel their order"""

       subject = f"Order Cancelled :# {str(email_data.order_id)[:8]}"

       message = f"""
       Hi {email_data.first_name},
       As requested, we have cancelled your order.
       """
       strategy.send(subject, message, email_data.email)

def send_payment_success_email(email_data, strategy: NotificationStrategy = EmailNotificationStrategy()):
       """Sends an email when the Payment is successfully confirmed"""

       subject = f"Payment Received for Order #{str(email_data.order_id)[:8]}"

       #Formating the date 
       payment_date = datetime.now().strftime("%b %d,%Y")
       try:
              method = email_data.payment_method
       except Exception:
              method = "Cod/Online"
       message =  f"""
       Hi {email_data.first_name},
       we have sucessfully recieved your payemen of ₹{email_data.total_price}
       
       Your order is now being processed and will be shipped soon
       
       ------------------------------------
       PAYMENT RECEIPT
       ------------------------------------
       
       Order ID: {email_data.order_id}
       Amount Paid: ₹{email_data.total_price}
       Date: {payment_date}
       Payment Method: {method }
       -------------------------------------------
       """
       strategy.send(subject, message, email_data.email)
       
