import logging
import json
from django.core.cache import cache
from . import repositories as default_repo
from .strategies import SearchStrategy, RedisSearchStrategy
import logging

logger = logging.getLogger(__name__)

def rebuild_search_index(repo = default_repo):

       products = repo.get_products_for_search_index() 
       # Logic: 
       processed_products = [
              {
                     "id": p['id'],
                     "name": p['name'],
                     "price": float(p['price']),
                     "brand": p['brand'],  # Convert Decimal to float for JSON
                     "slug" : p['slug']
              } 
              for p in products
       ]

       
       json_data = json.dumps(processed_products)

       cache.set('cqrs:product_catalog',json_data,timeout=None)

       logger.info(f"CQRS index Rebuilt:{len(products)} products cached in Redis")




def fast_search_catalog(search_term, strategy: SearchStrategy = RedisSearchStrategy(), repo=default_repo):
       

       """
       DEPENDENCY INVERSION: The service doesn't care if it's Redis or Postgres!
       """
       return strategy.search(search_term, repo)

       






