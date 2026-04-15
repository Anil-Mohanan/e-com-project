from .models import Order , OrderEventOutbox
from .tasks import task_send_payment_success_email
from django.db import transaction
from django.utils import timezone

def get_order_details_for_payment(order_id , user):
       try:
              order = Order.objects.get(order_id=order_id,user=user)#looking for an order that mateches the ID and belongs to this spefic user 
       except Order.DoesNotExist:
              raise ValueError("Order not Found")
       
       if order.is_paid:
              raise ValueError("This order  is already Paid")

       return {
              'order_id': order.order_id,
              'total_price': order.total_price
       }

def confirm_order_payment(order_id):
       try:
              order = Order.objects.get(order_id = order_id)
              if order.is_paid:
                     return
       except Order.DoesNotExist:
              raise ValueError("Order does not exist")

       order.status = 'OrderConfirmed'
       order.is_paid = True
       order.paid_at = timezone.now()
       order.save()

       items = order.items.all()
       OrderEventOutbox.objects.create(
              event_type = 'order.completed',
              payload = {
                     "user_id" : order.user_id,
                     "items" : [{'product_id': item.product_id} for item in items]
              }
       )

       transaction.on_commit(lambda:task_send_payment_success_email.delay(order.order_id))

