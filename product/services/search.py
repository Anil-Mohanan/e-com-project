import json
from django.core.cache import cache
from product.repositories import core as default_repo
from product.domain import SearchStrategy, RedisSearchStrategy
from product.events import product_event_bus, ProductSearched
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




def fast_search_catalog(search_term, strategy: SearchStrategy = RedisSearchStrategy(), repo=default_repo, user_id = None, session_key = None):


       """
       DEPENDENCY INVERSION: The service doesn't care if it's Redis or Postgres!
       """
       results = strategy.search(search_term, repo)

       # Only track non-empty search terms - don't log blank queries

       if not results and search_term and search_term.strip():
              from product.services.vector_search import semantic_search

              logger.info(f"No keyword match for '{search_term}' , Falling back to semantic search....")

              semantic_product_ids = semantic_search(query=search_term, top_k=5)
              # GET the IDs of simplar product from the pinecone

              if semantic_product_ids:

                     products = repo.get_products_for_search_index()

                     results = [p for p in products if p['id'] in semantic_product_ids]


       if search_term and search_term.strip():

              product_event_bus.publish(ProductSearched(payload={
                     "query" : search_term.strip(),
                     "user_id": user_id,
                     "session_key": session_key,
                     "result_count" : len(results) if isinstance(results, list) else 0,
              }))

       return results



       






