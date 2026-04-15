import logging
import json
from django.core.cache import cache
from .models import Product
import logging

logger = logging.getLogger(__name__)

def rebuild_search_index():

       products = list(Product.objects.filter(is_active = True).values('id','name','slug','price','brand')) #Why .values()? Standard Django QuerySets return heavy Python class objects that cannot be easily converted to JSON strings. .values() strips away all the Django bloat and returns raw, lightning-fast dictionaries.

       json_data = json.dumps(products)

       cache.set('cqrs:product_catalog',json_data,timeout=None)

       logger.info(f"CQRS index Rebuilt:{len(products)} products cached in Redis")




def fast_search_catalog(search_term):

       """
       This is O(n) — acceptable for catalogs under ~5,000 products
       For larger catalogs, this should be replaced with Elasticsearch or Redis Search (RediSearch)
       The PostgreSQL full-text search in get_queryset is the production-grade path; this is the fast/lightweight alternative

       """

       cache_catalog = cache.get('cqrs:product_catalog')

       if not cache_catalog:
              rebuild_search_index()

              cache_catalog = cache.get('cqrs:product_catalog')
       
       catalog = json.loads(cache_catalog)

       if not search_term:
              return catalog[:20]
       search_term = search_term.lower()
       result = []

       for item in catalog:
              name_match = item['name'] and search_term in item['name'].lower()
              brand_match = item['brand'] and search_term in item['brand'].lower()

              if name_match or brand_match:
                     result.append(item)

       return result[:20]






