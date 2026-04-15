from .models import Product

def get_active_products_count():
       
       total_product = Product.objects.filter(is_active = True).count()

       return total_product

def get_low_stock_product_data():

       low_stock_products = Product.objects.filter(
              stock___lte = 5,
              is_active = True
       ).values('id','name','stock','price')

       return list(low_stock_products)
         
