from celery import shared_task
from django.core.cache import cache
from orders.services.analytics import get_dashboard_order_metrics
from product.analytics_services import get_active_products_count
from .user_services import get_total_customers_count
import logging

logger = logging.getLogger(__name__)

@shared_task
def precompute_dashboard_statistics():
       logger.info("Starting scheduled dashboard pre-comutation")

       try:
              order = get_dashboard_order_metrics()
              total_revenue = order['total_revenue']
              total_order = order['total_orders']

              data = {
                     "total_revenue": total_revenue,
                     "total_orders" : total_order,
                     "total_products" : get_active_products_count(),
                     "total_users" : get_total_customers_count()
              }
              cache.set('dashboard_summary',data,timeout = 3600)
              logger.info("scheduled dashboard pre-computation successfull")

       except Exception as e:
              logger.error(f"scheduled dashboard pre-comutation failed: {e}")
