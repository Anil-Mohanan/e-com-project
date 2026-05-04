from .bus import DomainEvent, EventBus, product_event_bus


# ─────────────────────────────────────────────
# Product Domain Events — past tense (facts, not commands)
# ─────────────────────────────────────────────

class ProductViewed(DomainEvent):
    """
    Fired when a user opens a product detail page.
    Payload: { product_id, user_id (or None), session_key }
    """
    event_name = "product.viewed"


class ProductSearched(DomainEvent):
    """
    Fired when a user runs a search query.
    Payload: { query, user_id (or None), session_key, result_count }
    """
    event_name = "product.searched"


class ProductAddedToCart(DomainEvent):
    """
    Fired when a product is added to a user's cart.
    Published by the orders service (cart logic lives there),
    handled here in the product domain (behavior tracking lives here).
    Payload: { product_id, user_id, quantity }
    """
    event_name = "product.added_to_cart"


__all__ = [
    "DomainEvent",
    "EventBus",
    "product_event_bus",
    "ProductViewed",
    "ProductSearched",
    "ProductAddedToCart",
]
