from product.repositories import core as default_repo
import logging


logger = logging.getLogger('product')

def get_product_price(product_id: int, variant_id: int = None, repo = default_repo) -> float:

       return repo.get_product_price(product_id,variant_id)

def reserve_inventory(product_id:int,quantity:int, variant_id: int = None, repo = default_repo) -> bool:
       
       return repo.reserve_inventory(product_id,quantity,variant_id)

def deduct_inventory_for_order(items_data,repo = default_repo):
       
       return repo.deduct_inventory_for_order(items_data)
       
def restore_inventory_for_order(items_data,repo = default_repo):

       return repo.restore_inventory_for_order(items_data)



def add_review_process(product_id, user_id, rating, comment, repo=default_repo):
    if repo.user_already_reviewed(product_id, user_id):
        raise ValueError("You have already reviewed this Product")
        
    if not repo.user_has_purchased(product_id, user_id):
        raise ValueError("You can only review products you have purchased.")
        
    repo.create_review(product_id, user_id, rating, comment)
    logger.info(f"User {user_id} added a {rating}-star review to product {product_id}")
    return True


def build_comparison_matrix(product_ids_string,repo = default_repo):
       try:
              id_list = [int(i.strip()) for i in product_ids_string.split(',')]
       except (ValueError, AttributeError):
              raise ValueError("Invalid Product IDs provided. Use fromat ? id= 1,2,3" )

       if not id_list:
              raise ValueError("No product ID's provided")
       
       if len(id_list) > 4:
              raise ValueError("You can only compare up to 4 products at a time.")
       
       products = repo.get_product_by_ids(id_list)

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

def get_product_details(product_id: int, repo=default_repo) -> dict:
       return repo.get_product_details(product_id)
       

def add_product_stock(product_id, quantity, variant_id=None,repo = default_repo): # Add variant_id

       repo.add_product_stock(product_id,quantity,variant_id)


