from . import repositories as default_repo

def get_active_products_count(repo = default_repo):
       
       return repo.get_active_products_count()

def get_low_stock_product_data(repo = default_repo): 

       low_stock_products = repo.get_low_stock_products()

       return list(low_stock_products)
         
