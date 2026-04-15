from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product , Category, ProductVariant, Review
from .tasks import task_rebuild_search_index
from django.core.cache import cache

@receiver(post_save,sender=Product)
@receiver(post_delete,sender=Product)
def invalidate_product_cache(sender,instance,**kwargs):
       task_rebuild_search_index.delay()
       cache.delete(f"product_detail_{instance.slug}")
       try:
              cache.incr("product_list_version")
       except ValueError:
              cache.set("product_list_version",1,timeout=None)

@receiver(post_save,sender=Category)
@receiver(post_delete,sender=Category)
def invalidate_category_cache(sender,instance,**kwargs):

       cache.delete(f"category_detail_{instance.slug}")
       try:
              cache.incr("category_list_version")
       except ValueError:
              cache.set("category_list_version",1,timeout=None)


@receiver(post_save,sender=ProductVariant)
@receiver(post_delete,sender=ProductVariant)
def invalidate_productvariant_cache(sender,instance,**kwargs):
       cache.delete(f"product_variant_detail_{instance.id}")
       try:
              cache.incr("product_variant_list_version")
       except ValueError:
              cache.set("product_variant_list_version",1,timeout=None)
              
@receiver(post_save,sender = Review)
@receiver(post_delete,sender = Review)
def invalidate_review_cache(sender,instance,**kwargs):
       cache.delete(f"review_detail_{instance.id}")
       try:
              cache.incr("review_list_version")
       except ValueError:
              cache.set("review_list_version",1,timeout=None)
       