from .models import Product, ProductImages, ProductVariant, Category, Review, InventoryUnit
from django.db import transaction
import logging

logger = logging.getLogger('product')

def get_product_price(product_id: int, variant_id: int = None) -> float:
       
       product = Product.objects.get(id = product_id)

       final_price = product.price

       if variant_id:
     
              product_variant = ProductVariant.objects.get(id = variant_id)
       
              final_price += product_variant.price_adjustment

       return final_price

def reserve_inventory(product_id:int,quantity:int, variant_id: int = None) -> bool:
       with transaction.atomic():
              product = Product.objects.select_for_update().get(id = product_id)

              if product.stock < quantity: 
                     return False
              inventoryunit = InventoryUnit.objects.select_for_update().filter(product_id = product_id, variant_id = variant_id, status = 'In Stock')[:quantity]


              for units in inventoryunit:
                     units.status = 'Reserved'
                     units.save()
              product.stock -= quantity
              product.save()

              return True

def deduct_inventory_for_order(items_data):
       product_ids = [item ['product_id'] for item in items_data] # getting only the product_id from the dict items_data. items_data contain [{"product_id": 1 , "quantity" : 2} {"product_id: 10" , "quantity": 1}] that are marked cart in the order 
       products = Product.objects.select_for_update().filter(id__in = product_ids ).order_by('id') #Getting the products that from the db using that ids.
       locked_products_dict = {p.id: p for p in products} # this will look like this locked_products_dict =    2: "Shirt",5: "Shoes",8: "Watch" }
       for item in items_data:
              product = locked_products_dict[item['product_id']]
              available_units = list(InventoryUnit.objects.select_for_update().filter(product_id = item ['product_id'], status = 'In Stock')[:item['quantity']])
              if len(available_units) < item['quantity']:
                     raise ValueError(f"Sorry , {product.name} is out of stock.")
              for unit in available_units:
                     unit.status = 'Sold'
              InventoryUnit.objects.bulk_update(available_units,['status'])
              product.stock -= item['quantity']
              product.save()

       return {p.id:p.price for p in products}
       
def restore_inventory_for_order(items_data):
       product_ids = [item ['product_id'] for item in items_data]

       products = Product.objects.select_for_update().filter(id__in = product_ids).order_by('id')

       locked_products_dict = {p.id: p for p in products}

       for item in items_data:
              product = locked_products_dict[item['product_id']]

              sold_units = list(InventoryUnit.objects.select_for_update().filter(product_id = item ['product_id'],status = 'Sold')[:item['quantity']])

              for unit in sold_units:
                     unit.status = 'In Stock'
              InventoryUnit.objects.bulk_update(sold_units,['status'])
              product.stock += item['quantity']
              product.save()



def add_review_process(product,user,rating,comment):
       reveiw = Review.objects.create(
                     product = product,
                     user = user,
                     rating= rating,
                     comment = comment
              )
       logger.info(f"User {user.id} added a {rating}-star review to product {product.id}")

       return reveiw

def build_comparison_matrix(product_ids_string):
       try:
              id_list = [int(i.strip()) for i in product_ids_string.split(',')]
       except (ValueError, AttributeError):
              raise ValueError("Invalid Product IDs provided. Use fromat ? id= 1,2,3" )

       if not id_list:
              raise ValueError("No product ID's provided")
       
       if len(id_list) > 4:
              raise ValueError("You can only compare up to 4 products at a time.")
       
       products = Product.objects.filter(id__in= id_list,is_active=True)

       if len(products) < 2:
              raise ValueError("Need at least 2 valid products to compare.")

       comparsion_data = {
              'products' : [],
              'specifications' : {}
       }

       for prod in products:

              comparsion_data['products'].append({
                     'id' : prod.id,
                     'name': prod.name,
                     'price': str(prod.price),
                     'brand': prod.brand
              })   

              for spec_key, spec_value in prod.specifications.items():

                     if spec_key not in comparsion_data['specifications']:

                            comparsion_data['specifications'][spec_key] = {}

                     comparsion_data['specifications'][spec_key][prod.id] = spec_value
                     
       logger.info(f"Successfully build comparsion matrix for {len(id_list)} products: {id_list}")

       return comparsion_data

def get_product_details(product_id: int) -> dict:
       
       product = Product.objects.get(id=product_id)

       return {
              "name": product.name,
              "price" : product.price
       }