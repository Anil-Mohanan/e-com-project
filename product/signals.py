
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product , Category, ProductVariant, Review
from .tasks import task_rebuild_search_index, task_sync_product_embedding
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

@receiver(post_save, sender = Product)
def sync_embedding_on_save(sender, instance,**kwargs):
       #@receiver(post_save, sender=Product) - Django calls this function
       # every time any product raw is saved , whether it's new product or an update

       # only sync active products
       if not instance.is_active:
              return
              # return here exits the function early - Celery task is never called for inactive products
       task_sync_product_embedding.delay(
              product_id = instance.id,
              # instance.id is the integer primary key — what Pinecone uses as the vector ID
              name = instance.name,
              brand = instance.brand or "", 
              # instance.brand can be None (nullable field) — we pass "" to avoid crashing the embedding
              description = instance.description,
       )
       
              
@receiver(post_save,sender = Review)
@receiver(post_delete,sender = Review)
def invalidate_review_cache(sender,instance,**kwargs):
       cache.delete(f"review_detail_{instance.id}")
       try:
              cache.incr("review_list_version")
       except ValueError:
              cache.set("review_list_version",1,timeout=None)
       