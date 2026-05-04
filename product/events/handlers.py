import logging
from product.models import ProductBehaviorLog

logger = logging.getLogger("product.events.handlers")


# ─────────────────────────────────────────────
#  product.viewed handlers
# ─────────────────────────────────────────────

def handle_log_product_view(payload: dict) -> None:
    """
    Single responsibility: write one row to ProductBehaviorLog.
    This is the raw data feed the analytics layer queries later.
    """
    ProductBehaviorLog.objects.create(
        event_type="product.viewed",
        product_id=payload.get("product_id"),
        user_id=payload.get("user_id"),          # None for anonymous users — that's fine
        session_key=payload.get("session_key"),
        metadata={},
    )
    logger.info(f"Logged product.viewed for product_id={payload.get('product_id')}")


# ─────────────────────────────────────────────
#  product.searched handlers
# ─────────────────────────────────────────────

def handle_log_product_search(payload: dict) -> None:
    """
    Logs search terms and result counts.
    Use case: find searches that return ZERO results — those are products you should add.
    """
    ProductBehaviorLog.objects.create(
        event_type="product.searched",
        product_id=None,                          # searches have no single product
        user_id=payload.get("user_id"),
        session_key=payload.get("session_key"),
        metadata={
            "query": payload.get("query", ""),
            "result_count": payload.get("result_count", 0),
        },
    )
    logger.info(f"Logged product.searched for query='{payload.get('query')}'")


# ─────────────────────────────────────────────
#  product.added_to_cart handlers
# ─────────────────────────────────────────────

def handle_log_product_added_to_cart(payload: dict) -> None:
    """
    Critical data point: if a product is viewed often but added to cart rarely,
    that signals a price or trust problem. This log lets you detect that pattern.
    """
    ProductBehaviorLog.objects.create(
        event_type="product.added_to_cart",
        product_id=payload.get("product_id"),
        user_id=payload.get("user_id"),
        session_key=None,                         # cart events always have a logged-in user
        metadata={
            "quantity": payload.get("quantity", 1),
        },
    )
    logger.info(
        f"Logged product.added_to_cart for "
        f"product_id={payload.get('product_id')} user_id={payload.get('user_id')}"
    )
