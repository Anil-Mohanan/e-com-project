from django.db import transaction
from product.models import Product, ProductVariant, InventoryUnit, Review,ProductPurchaseHistory,ProductBehaviorLog
from product.domain import ProductDTO
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
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

def get_all_product_ids():
    """
    Returns a flat list of all active product IDs.
    The nightly task iterates over this list to compute recommendations.
    Only active products — no point recommending unavailable items.
    """

    return list(Product.objects.filter(is_active = True).values_list('id', flat = True))

def get_low_stock_products():
    low_stock = Product.objects.filter(stock__lte=5, is_active=True)
    return [_to_entity(p) for p in low_stock]

def get_products_for_search_index():
    # .values() returns fast dictionaries for Redis caching instead of heavy Django Models
    return list(Product.objects.filter(is_active=True).values('id', 'name', 'slug', 'price', 'brand','images__image'))

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
    if variant_id:
        product_variant = ProductVariant.objects.get(id = variant_id)
        return product_variant.price
    
    product = Product.objects.get(id = product_id)
    return product.price

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

def deduct_inventory_for_order(items_data,order_id):

    with transaction.atomic():
            product_ids = [item['product_id'] for item in items_data]
            products = Product.objects.select_for_update().filter(id__in=product_ids).order_by('id')
            locked_products_dict = {p.id: p for p in products}

            all_units_to_update = []

            for item in items_data:
                product = locked_products_dict[item['product_id']]
                product.stock -= item['quantity']
                available_units = list(InventoryUnit.objects.select_for_update().filter(product_id=item['product_id'],status='In Stock')[:item['quantity']])
                all_units_to_update.extend(available_units)

                if len(available_units) < item['quantity']:
                   raise ValueError(f"Sorry, {product.name} is out of stock.")

                for unit in available_units:
                    unit.status = 'Sold'
                    unit.current_order_id = order_id
                    
                    
            InventoryUnit.objects.bulk_update(all_units_to_update, ['status','current_order_id'])
            Product.objects.bulk_update(products, ['stock'])
    

            return {p.id: p.price for p in products}

def restore_inventory_for_order(items_data,order_id):

    with transaction.atomic():

        product_ids = [item['product_id'] for item in items_data]
        products = Product.objects.select_for_update().filter(id__in=product_ids).order_by('id')
        locked_products_dict = {p.id: p for p in products}

        all_units = []

        for item in items_data:
            product = locked_products_dict[item['product_id']]
            sold_units = list(InventoryUnit.objects.select_for_update().filter(product_id=item['product_id'],current_order_id = order_id))
            product.stock += len(sold_units)
            all_units.extend(sold_units)
            for unit in sold_units:
                unit.status = 'In Stock'
                unit.current_order_id = None
                

        InventoryUnit.objects.bulk_update(all_units, ['status','current_order_id'])
        Product.objects.bulk_update(products,['stock'])

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

def get_review_by_id(review_id):
    return Review.objects.get(id = review_id)

def update_review(review_id, rating, comment):
    review = Review.objects.get(id=review_id)
    if rating:
        review.rating = rating
    if comment:
        review.comment = comment
    review.save()
    return review


def user_already_reviewed(product_id, user_id):

       return Review.objects.filter(product_id = product_id,user_id = user_id).exists()

def user_has_purchased(product_id,user_id):

       return ProductPurchaseHistory.objects.filter(product_id = product_id,user_id = user_id).exists()




#==========================================
#Behaviro Analytics Repository Methods
#==========================================

def log_product_behavior(event_type:str, product_id: int, user_id: int, session_key: str, metadata: dict = None):
    # Encapsulates the model creation so services/handlers don't depend on the ORM
    return ProductBehaviorLog.objects.create(
        event_type = event_type, 
        product_id = product_id, 
        user_id = user_id,
        session_key = session_key,
        metadata = metadata or {}
        # metadata or {} ensure we alwasy save dict even if None is passed
    )

def get_trending_products(days = 7 , limit = 10):
    """Question: What products are users viewing the most this week?

        filter ProductBehaviorLog to the last N days, count views per product,
        order by view count descending, and return the top N product IDs with counts.
        .values('product_id') -> Group BY product_id
        .annotate(view_count = Count('id')) -> COUNT(*) per group

    """
    since = timezone.now() - timedelta(days = days)

    trending_ids = (
        ProductBehaviorLog.objects.filter(event_type = 'product.viewed',created_at__gte = since, product_id__isnull = False).values('product_id').annotate(view_count = Count('id')).order_by('-view_count')[:limit].values_list('product_id',flat = True)
    )

    return list(
        Product.objects.filter(id__in = trending_ids, is_active = True).prefetch_related('images')
    )

def get_cart_abandonment_data(days= 30, min_views=3):
    """
        Which products are viewd a lot but rarely added to cart
        Hight views + low cart adds = price problem , trust problem, or bad UX.
        Compute the ratio: cart_adds/ views. Lower ratio = more abandoned.
        
        return products where view count exceeds min_views threshold,don't flag products that were just viewed once or twice.

    """
    since = timezone.now() - timedelta(days = days)

    views = (
        ProductBehaviorLog.objects.filter(event_type = 'product.viewed',created_at__gte =since, product_id__isnull = False).values('product_id').annotate(view_count=Count('id'))
    )
    cart_adds = (
        ProductBehaviorLog.objects.filter(
            event_type = 'product.added_to_cart',created_at__gte = since, product_id__isnull = False
        ).values('product_id').annotate(cart_count = Count('id'))
    )

    # build a look up dict so that can merge the two querysets in pyhon
    # Djanog ORM Cannot easily JOIN two aggregated querysets directily

    views_dict = {row['product_id']: row['view_count'] for row in views}
    cart_dict = {row['product_id']: row['cart_count'] for row in cart_adds}

    result = []

    for product_id, view_count in views_dict.items():
        if view_count < min_views:
            continue # ignore products with too few views to be meaningful
        cart_count = cart_dict.get(product_id,0)
        # conversion_rate: what % of viewers also added to cart

        conversion_rate = round((cart_count/ view_count) * 100, 1)

        result.append({
            'product_id': product_id,
            'view_count': view_count,
            'cart_count': cart_count,
            'conversion_rate': conversion_rate,
        })

    # Sort by conversion_rate ascending - most abandoned prodcuts first

    return sorted(result, key= lambda x: x['conversion_rate'])

def get_zero_result_searches(days = 30, limit= 20):
    """What are users searching for that reutrns nothing
    Theser are categlog gaps - products should be stocking.
    filter for search events where result_conut is metadata is 0,
    then count how many time each query was searched.
    """

    since = timezone.now() - timedelta(days = days)

    return list(
        ProductBehaviorLog.objects.filter(
            event_type = 'product.searched',
            created_at__gte = since,
            metadata_result_count = 0,
            # JONSField lookup - queries the metadata Json key
        ).values('metadata__query')#group by query string inside the JSON
        .annotate(search_count = Count('id'))
        .order_by ('-search_count')[:limit]
    )

def get_frequently_viewed_together(product_id, days=30, limit=5):
    """
    Question: What other products do users look at in the same session?
    
    We find all session_keys that viewed this product,
    then find what OTHER products those same sessions also viewed.
    This gives us "customers who viewed this also viewed..." data.
    
    This is a 2-step query:
    Step 1: Find all sessions that viewed the target product
    Step 2: Find all OTHER products those sessions viewed
    """
    since = timezone.now() - timedelta(days=days)
    # Step 1: get session keys of users who viewed this product
    sessions_that_viewed = (
        ProductBehaviorLog.objects
        .filter(
            event_type='product.viewed',
            product_id=product_id,
            created_at__gte=since,
            session_key__isnull=False,  # only sessions we can track
        )
        .values_list('session_key', flat=True)
        .distinct()
    )
    if not sessions_that_viewed:
        return []
    # Step 2: find other products those same sessions viewed
    related_ids = (
                ProductBehaviorLog.objects
        .filter(
            event_type='product.viewed',
            session_key__in=sessions_that_viewed,
            created_at__gte=since,
        )
        .exclude(product_id=product_id)  # exclude the product itself
        .values('product_id')
        .annotate(co_view_count=Count('id'))
        .order_by('-co_view_count')[:limit]
        .values_list('product_id',flat=True)
    )
    return list(
        Product.objects.filter(id__in = related_ids, is_active = True).prefetch_related('images')
    )


#==================================================
# Recommendation Repository Methods
#==================================================

def save_recommendations(source_product_id,recommendations):
    """
    Writes pre-computed recommendations to the ProductRecommendation table.
    Called only by the nightly Celery task - never by a live request.
    'recommedation' is a list of dicts: [{'product_id': X, 'score': Y.Z},....]

    """

    from product.models import ProductRecommendation # Local import to avoid circular import at module load time

    for rec in recommendations:
        #update_or_create: if the pair already exists, update score + computed_at.
        # if it's new , create it . This make the task safely re-runnable (idempontent).

        ProductRecommendation.objects.update_or_create(
            source_product_id = source_product_id,
            recommended_product_id = rec['product_id'],# The product being recommended
            defaults = {'score': rec['score']} # only 'score' is updated if the row already exists
        )

def get_precomputed_recommendations(product_id,limit = 5):

    """
    Read pre-computed recommednations from the ProductRecommendation table.
    This is the fast path - one indexed lookup, no aggregation, no GROUP By.
    Returns a list of Product_ids orderd by score descending.

    """

    from product.models import ProductRecommendation, Product
    # Get the IDs of the recommended products from the pre-computed table
    related_ids = ProductRecommendation.objects.filter(
        source_product_id = product_id
    ).values_list('recommended_product_id',flat=True)[:limit]
    # Fetch actual Product objects for those IDs
    # This enusre the seralizer get the 'name', 'price', and 'image'  it needs!

    return list(
            Product.objects.filter(id__in = related_ids, is_active = True).prefetch_related('images')
    )