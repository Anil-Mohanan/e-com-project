import json
from django.core.cache import cache
from product.repositories import core as default_repo
from product.domain import SearchStrategy, RedisSearchStrategy
from product.events import product_event_bus, ProductSearched
import logging

logger = logging.getLogger(__name__)

def rebuild_search_index(repo = default_repo):

       products_raw = repo.get_products_for_search_index() 
    
       # We use a dictionary to deduplicate products (one image per product)
       indexed_data = {}
       for p in products_raw:
              pid = p['id']
              if pid not in indexed_data:
                  indexed_data[pid] = {
                      "id": pid,
                      "name": p['name'],
                      "price": float(p['price']),
                      "brand": p['brand'],
                      "slug": p['slug'],
                      "image": p['images__image'] # Grab the first image that find
                  }
       json_data = json.dumps(list(indexed_data.values()))
       cache.set('cqrs:product_catalog', json_data, timeout=None)
       logger.info(f"CQRS index Rebuilt: {len(indexed_data)} products cached in Redis")



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



       






