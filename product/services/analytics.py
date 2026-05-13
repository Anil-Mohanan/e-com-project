import logging
from product.repositories import core as default_repo

logger = logging.getLogger('product.analytics')

def get_active_products_count(repo = default_repo):
       
       return repo.get_active_products_count()

def get_low_stock_product_data(repo = default_repo): 

       low_stock_products = repo.get_low_stock_products()

       return list(low_stock_products)
         
def get_trending_products_service(days = 7, limit = 10, repo = default_repo):
       """
       Returns the most-viewed products in the Last N days.
       Using for a "Trending Now" section on the frontend.
       """
       data = repo.get_trending_products(days = days, limit = limit)
       logger.info(f"Trending query returned {len(data)} products for last {days} days")
       return data

def get_cart_abandonment_report(days = 30, min_views = 3, repo = default_repo):
       """
       Returns products that are viewed often but rearely added to cart
       A low conversion_rate singals a price, trust or UX problem.
       """
       data = repo.get_cart_abandonment_data(days = days,min_views = min_views)
       logger.info(f"Cart abandonement report: {len(data)} product analysed"),
       return data

def get_zero_result_searches_service(days = 30, limit = 20, repo = default_repo):
       """
       Returns search queries that found nothing. These are direct singals for which products
       to the categlog
       """

       data = repo.get_zero_result_searches(days = days, limit = limit)
       logger.info(f"Zero-result searches: {len(data)} distinct queries found")
       return data

def get_related_products_service(product_id, days = 30 , limit = 5,repo = default_repo):
       """
       Two-path strategy
       1. Fast path: read from productRecommendation(pre-computed nightly)
       2. Fallback: run live query on  productBehaviroLog if no pre-compouted data exists
       This means the API is fast in product And still works on Day 1 Before the first nightly task has run.
       """

       precomputed = repo.get_precomputed_recommendations(product_id = product_id, limit = limit)
       # happy path in production -sub millisecond reponse
       if precomputed:
              
              logger.info(f"Serving pre-computed recommedation for product {product_id}")
              return precomputed


       logger.info(f"No pre-computed data for product {product_id} — running live query")
       data = repo.get_frequently_viewed_together(product_id=product_id, days=days, limit=limit)
       return data
