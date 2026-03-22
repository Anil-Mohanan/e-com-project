from .models import Product, ProductImages, ProductVariant, Category, Review, InventoryUnit

import logging

logger = logging.getLogger('product')



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
                     
       logger.info(f"Successfully build comparsion matrix for {len(len_list)} products: {id_list}")

       return comparsion_data
