from celery import shared_task
from django.core.cache import cache
from django.db.models import Sum
from django.contrib.auth import get_user_model
from orders.models import Order
from product.models import Product
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task
def precompute_dashboard_statistics():
       logger.info("Starting scheduled dashboard pre-comutation")

       try:
              valid_order = Order.objects.valid_sales()# what is valid_sales did i made this or it's is an inbuild option how does it going to check for orders that is valid without any paramter inside

              revenue_data = valid_order.aggregate(Sum('total_price'))

              data = {
                     "total_revenue":revenue_data['total_price__sum'] or 0,
                     "total_orders" : valid_order.count(),
                     "total_products" : Product.objects.filter(is_active=True).count(),
                     "total_users" : User.objects.filter(is_staff = False).count()
              }
              cache.set('dashboard_summary',data,timeout = 3600)
              logger.info("scheduled dashboard pre-computation successfull")

       except Exception as e:
              logger.error(f"scheduled dashboard pre-comutation failed: {e}")
