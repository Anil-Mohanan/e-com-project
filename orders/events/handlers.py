import logging
from orders.infrastructure.tasks import (
    task_send_order_confirmation_email,
    task_send_shipping_email,
    task_cancellation_email,
    task_send_payment_success_email,
)
from orders.repositories import core as repo

logger = logging.getLogger("orders.events.handlers")


# ─────────────────────────────────────────────
#  order.placed handlers
# ─────────────────────────────────────────────

def handle_send_order_confirmation_email(payload: dict) -> None:
    """
    Handler #1 for OrderPlaced.
    Single responsibility: send the confirmation email only.
    It knows nothing about inventory, analytics, etc.
    """
    order_id = payload.get("order_id")
    task_send_order_confirmation_email.delay(order_id)
    logger.info(f"Queued confirmation email for order {order_id}")


def handle_publish_placed_event_to_outbox(payload: dict) -> None:
    """
    Handler #2 for OrderPlaced.
    Single responsibility: write the event into the outbox for cross-domain fan-out.
    The sweep_order_outbox Celery task will pick this up and route it to the
    product domain (inventory deduction), analytics, etc.
    """
    repo.create_outbox_event("order.placed", payload)
    logger.info(f"Outbox event 'order.placed' created for order {payload.get('order_id')}")


# ─────────────────────────────────────────────
#  order.cancelled handlers
# ─────────────────────────────────────────────

def handle_send_cancellation_email(payload: dict) -> None:
    """Handler for OrderCancelled: sends cancellation email."""
    order_id = payload.get("order_id")
    task_cancellation_email.delay(order_id)
    logger.info(f"Queued cancellation email for order {order_id}")


def handle_publish_cancelled_event_to_outbox(payload: dict) -> None:
    """Handler for OrderCancelled: writes to outbox for product domain to restore stock."""
    repo.create_outbox_event("order.cancelled", payload)
    logger.info(f"Outbox event 'order.cancelled' created for order {payload.get('order_id')}")


# ─────────────────────────────────────────────
#  order.paid handlers
# ─────────────────────────────────────────────

def handle_send_payment_success_email(payload: dict) -> None:
    """Handler for OrderPaid: sends payment success email."""
    order_id = payload.get("order_id")
    task_send_payment_success_email.delay(order_id)
    logger.info(f"Queued payment success email for order {order_id}")


def handle_publish_completed_event_to_outbox(payload: dict) -> None:
    """Handler for OrderPaid: writes to outbox for analytics domain."""
    repo.create_outbox_event("order.completed", payload)
    logger.info(f"Outbox event 'order.completed' created for order {payload.get('order_id')}")


# ─────────────────────────────────────────────
#  order.shipped handlers
# ─────────────────────────────────────────────

def handle_send_shipping_email(payload: dict) -> None:
    """Handler for OrderShipped: sends shipping notification email."""
    order_id = payload.get("order_id")
    task_send_shipping_email.delay(order_id)
    logger.info(f"Queued shipping email for order {order_id}")
