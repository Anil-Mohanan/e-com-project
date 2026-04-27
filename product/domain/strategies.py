import json
from abc import ABC, abstractmethod
from django.core.cache import cache



class SearchStrategy(ABC):
       @abstractmethod
       def search(self,search_term: str, repo) -> list:
              pass

class RedisSearchStrategy(SearchStrategy):
       """
       This is O(n) — acceptable for catalogs under ~5,000 products
       For larger catalogs, this should be replaced with Elasticsearch or Redis Search (RediSearch)
       The PostgreSQL full-text search in get_queryset is the production-grade path; this is the fast/lightweight alternative
       """
       def search(self,search_term: str, repo) -> list:
              cache_catalog = cache.get('cqrs:product_catalog')

              if not cache_catalog:
                     from product.services import rebuild_search_index
                     rebuild_search_index(repo = repo)
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

class PostgresSearchStrategy(SearchStrategy):
       def search(self, search_term: str, repo) -> list:
              # Tomorrow, you can implement this by calling a repo method!
              # return repo.postgres_full_text_search(search_term)
              pass