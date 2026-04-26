from django.db import transaction
from .models import Product, ProductVariant, InventoryUnit, Review,ProductPurchaseHistory
from .domain import ProductDTO
import uuid

# ==========================================
# Domain Transfer Object Helpers
# ==========================================

def _to_entity(product) -> ProductDTO:
    return ProductDTO(
       id=product.id,
       name=product.name,
       stock=product.stock,
       price=product.price,
       brand=product.brand,
       specifications=product.specifications
    )

# ==========================================
# Analytics & Search Repository Methods
# ==========================================

def get_active_products_count():
    return Product.objects.filter(is_active=True).count()

def get_low_stock_products():
    low_stock = Product.objects.filter(stock__lte=5, is_active=True)
    return [_to_entity(p) for p in low_stock]

def get_products_for_search_index():
    # .values() returns fast dictionaries for Redis caching instead of heavy Django Models
    return list(Product.objects.filter(is_active=True).values('id', 'name', 'slug', 'price', 'brand'))

# ==========================================
# Product Core Repository Methods
# ==========================================

def get_product_by_ids(id_list):
    products = Product.objects.filter(id__in=id_list, is_active=True)
    return [_to_entity(p) for p in products]

def get_product_details(product_id):
    product = Product.objects.get(id=product_id)
    return {
       "name": product.name,
       "price": product.price
    }

def get_product_price(product_id, variant_id):
    product = Product.objects.get(id=product_id)
    final_price = product.price

    if variant_id:
       product_variant = ProductVariant.objects.get(id=variant_id)

       if final_price < product_variant.price_adjustment:
           final_price += product_variant.price_adjustment
     

    return final_price

def create_review(product_id, user_id, rating, comment):
    return Review.objects.create(
       product_id=product_id, 
       user_id=user_id,
       rating=rating,
       comment=comment
    )

# ==========================================
# Inventory Transaction Repository Methods 
# ==========================================

def add_product_stock(product_id, quantity, variant_id):
    if quantity <= 0:
       raise ValueError("Quantity must be positive and greater than zero")

    with transaction.atomic():
       product = Product.objects.select_for_update().get(id=product_id)
       # Logic for Variant Support
       variant = None
       if variant_id:
           variant = ProductVariant.objects.get(id=variant_id)
       # Create units WITH the variant link
       units = [
           InventoryUnit(
               product=product, 
               variant=variant, 
               status='In Stock',
               serial_number=f"SN-{uuid.uuid4().hex[:10].upper()}"
           ) 
           for _ in range(quantity)
       ]
       InventoryUnit.objects.bulk_create(units)
       # Update the main counter
       product.stock += quantity
       product.save()

def reserve_inventory(product_id, quantity, variant_id):
    with transaction.atomic():
       product = Product.objects.select_for_update().get(id=product_id)
       if product.stock < quantity: 
           return False
       
       inventoryunit = InventoryUnit.objects.select_for_update().filter(
           product_id=product_id, 
           variant_id=variant_id, 
           status='In Stock'
       )[:quantity]
       
       for units in inventoryunit:
           units.status = 'Reserved'
           units.save()
           
       product.stock -= quantity
       product.save()
       return True

def deduct_inventory_for_order(items_data):
    product_ids = [item['product_id'] for item in items_data]
    products = Product.objects.select_for_update().filter(id__in=product_ids).order_by('id')
    locked_products_dict = {p.id: p for p in products}
    
    for item in items_data:
       product = locked_products_dict[item['product_id']]
       available_units = list(InventoryUnit.objects.select_for_update().filter(
           product_id=item['product_id'], 
           status='In Stock'
       )[:item['quantity']])
       
       if len(available_units) < item['quantity']:
           raise ValueError(f"Sorry, {product.name} is out of stock.")
           
       for unit in available_units:
           unit.status = 'Sold'
           
       InventoryUnit.objects.bulk_update(available_units, ['status'])
       product.stock -= item['quantity']
       product.save()

    return {p.id: p.price for p in products}

def restore_inventory_for_order(items_data):
    product_ids = [item['product_id'] for item in items_data]
    products = Product.objects.select_for_update().filter(id__in=product_ids).order_by('id')
    locked_products_dict = {p.id: p for p in products}

    for item in items_data:
       product = locked_products_dict[item['product_id']]
       sold_units = list(InventoryUnit.objects.select_for_update().filter(
           product_id=item['product_id'],
           status='Sold'
       )[:item['quantity']])
       for unit in sold_units:
           unit.status = 'In Stock'
           
       InventoryUnit.objects.bulk_update(sold_units, ['status'])
       product.stock += len(sold_units)
       product.save()

# ==========================================
# Task 
# ==========================================

def record_product_purchase(user_id,product_id):
       ProductPurchaseHistory.objects.get_or_create(
              user_id = user_id,
              product_id = product_id
       )


# ==========================================
# Views.py
# ==========================================

def user_already_reviewed(product_id, user_id):
       return Review.objects.filter(product_id = product_id,user_id = user_id).exists()

def user_has_purchased(product_id,user_id):
       return ProductPurchaseHistory.objects.filter(product_id = product_id,user_id = user_id).exists()