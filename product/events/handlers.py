import logging
from product.repositories import core as default_repo

logger = logging.getLogger("product.events.handlers")


# ─────────────────────────────────────────────
#  product.viewed handlers
# ─────────────────────────────────────────────

def handle_log_product_view(payload: dict,repo = default_repo) -> None:
    """
    Single responsibility: write one row to ProductBehaviorLog.
    This is the raw data feed the analytics layer queries later.
    """
    try:
        #pushing the db writ into the repo layer
        repo.log_product_behavior(
            event_type="product.viewed",
            product_id=payload.get("product_id"),
            user_id=payload.get("user_id"),          # None for anonymous users — that's fine
            session_key=payload.get("session_key"),
            metadata={},
        )
        logger.info(f"Logged product.viewed for product_id={payload.get('product_id')}")

    except Exception as e:
        logger.error(f"failed to log prodct.viewd event: {e}", exc_info = True)


# ─────────────────────────────────────────────
#  product.searched handlers
# ─────────────────────────────────────────────

def handle_log_product_search(payload: dict,repo = default_repo) -> None:
    """
    Logs search terms and result counts.
    Use case: find searches that return ZERO results — those are products you should add.
    """
    try:

        repo.log_product_behavior(
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
    
    except Exception as e:
        logger.error(f"Failed to log product.searched event: {e}", exc_info = True)# exc_info=True gives us the full stack trace in our logs so we can debug it later

# ─────────────────────────────────────────────
#  product.added_to_cart handlers
# ─────────────────────────────────────────────

def handle_log_product_added_to_cart(payload: dict,repo = default_repo) -> None:
    """
    Critical data point: if a product is viewed often but added to cart rarely,
    that signals a price or trust problem. This log lets you detect that pattern.
    """
    try:
        repo.log_product_behavior(
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
    except Exception as e:
        logger.error(f"Faild to log product.added_to_cart event: {e}", exc_info= True)
        