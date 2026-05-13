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
    try:
        order_id = payload.get("order_id")
        task_send_order_confirmation_email.delay(order_id)
        logger.info(f"Queued confirmation email for order {order_id}")
    except Exception as e:
        logger.error(f"Failed to queue confirmation email for order {payload.get('order_id')}: {e}", exc_info=True)


def handle_publish_placed_event_to_outbox(payload: dict) -> None:
    try:
        repo.create_outbox_event("order.placed", payload)
        logger.info(f"Outbox event 'order.placed' created for order {payload.get('order_id')}")
    except Exception as e:
        logger.error(f"Failed to create outbox event 'order.placed': {e}", exc_info=True)


# ─────────────────────────────────────────────
#  order.cancelled handlers
# ─────────────────────────────────────────────

def handle_send_cancellation_email(payload: dict) -> None:
    try:
        order_id = payload.get("order_id")
        task_cancellation_email.delay(order_id)
        logger.info(f"Queued cancellation email for order {order_id}")
    except Exception as e:
        logger.error(f"Failed to queue cancellation email for order {payload.get('order_id')}: {e}", exc_info=True)


def handle_publish_cancelled_event_to_outbox(payload: dict) -> None:
    try:
        repo.create_outbox_event("order.cancelled", payload)
        logger.info(f"Outbox event 'order.cancelled' created for order {payload.get('order_id')}")
    except Exception as e:
        logger.error(f"Failed to create outbox event 'order.cancelled': {e}", exc_info=True)


# ─────────────────────────────────────────────
#  order.paid handlers
# ─────────────────────────────────────────────

def handle_send_payment_success_email(payload: dict) -> None:
    try:
        order_id = payload.get("order_id")
        task_send_payment_success_email.delay(order_id)
        logger.info(f"Queued payment success email for order {order_id}")
    except Exception as e:
        logger.error(f"Failed to queue payment success email for order {payload.get('order_id')}: {e}", exc_info=True)


def handle_publish_completed_event_to_outbox(payload: dict) -> None:
    try:
        repo.create_outbox_event("order.completed", payload)
        logger.info(f"Outbox event 'order.completed' created for order {payload.get('order_id')}")
    except Exception as e:
        logger.error(f"Failed to create outbox event 'order.completed': {e}", exc_info=True)


# ─────────────────────────────────────────────
#  order.shipped handlers
# ─────────────────────────────────────────────

def handle_send_shipping_email(payload: dict) -> None:
    try:
        order_id = payload.get("order_id")
        task_send_shipping_email.delay(order_id)
        logger.info(f"Queued shipping email for order {order_id}")
    except Exception as e:
        logger.error(f"Failed to queue shipping email for order {payload.get('order_id')}: {e}", exc_info=True)
