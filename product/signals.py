from math import exp
import uuid
from django.db.models.signals import post_save, post_delete
from config.cache_utils import invalidate_cache
from django.dispatch import receiver
from .models import Product , Category, ProductVariant, Review, InventoryUnit,ProductImages
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
       

@receiver(post_save, sender = Product)# Tells the django to run the function below only  when a product models is saved
def sync_inventory_units(sender, instance, created, **kwargs):# This singal handler function. 'instance is the spcecific product being saved.
       #Count how many phsycical InventoryUnit currently exist in the DB for this specific Product
       exisiting_count = InventoryUnit.objects.filter(product=instance).count()
       #Calculate the difference between the aggregate stock number and the physical units
       needed = instance.stock - exisiting_count
       #checks if the admin incrased the stock (meaning need to create new physcial units)
       if needed > 0:
              
              new_units = []

              for _ in range(needed):
                     # Generate a unique serial number using the product ID and a random 8-character string
                     serial = f"SN-{instance.id}-{uuid.uuid4().hex[:8].upper()}"
                     # Creating a new physical InventoryUnit object in memeroy (not saved to the DB yet)
                     unit = InventoryUnit(product = instance, status="In Stock", serial_number = serial)

                     new_units.append(unit)

              #Using bulk create to save all the new units to the DB in one singal query
              InventoryUnit.objects.bulk_create(new_units)


@receiver([post_save, post_delete],sender = Product)
def invalidate_product_cache(sender,instance,**kwargs):
       # This fires the background search index update
       task_rebuild_search_index.delay()

       #It instantly "deletes" all old cache entires for new products.Product
       invalidate_cache("product_list")
       invalidate_cache("product_detail")

@receiver([post_save,post_delete],sender = ProductImages)
def invalidate_image_cache(sender, instance, **kwargs):
       #if an image is added/removed ,must clear the product detail caceh
       task_rebuild_search_index.delay()

       invalidate_cache("product_list")
       invalidate_cache("prodcut_detail")


@receiver([post_save, post_delete],sender = ProductVariant)
def invalidate_productvariant_cache(sender, instance, **kwargs):
       # 1 Clear the specific variant detail 
       cache.delete(f"product_variant_detail_{instance.id}")

       # clear the parent produt's cache!
       # the prodct detail page include the varain list,

       if instance.product:
              cache.delete(f"product_detail_{instance.product.slug}")

              invalidate_cache("product_list")
              invalidate_cache("product_detail")
       
       try:
              cache.incr("product_variant_list_version")
       except ValueError:
              cache.set("product_variant_list_version", 1, timeout = None)

@receiver([post_save,post_delete],sender = Review)
def invalidate_review_cache(sender, instance, **kwargs):
       # Clear the cache for the specific product detail page
       #(since the detail page shows the reviews)
       if instance.product:
              cache.delete(f"product_detail_{instance.product.slug}")
              invalidate_cache("review_list")
       # Clear the global version only if using global version only 

       try:
              cache.incr(f"reviews_version_{instance.product_id}")
       except ValueError:
              cache.set(f"reviews_version_{instance.product_id}", 1, timeout=None)