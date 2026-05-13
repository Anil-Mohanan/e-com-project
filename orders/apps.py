from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = 'orders'

    def ready(self):
        """
        This method runs once when django stats up . This is the Dependency Injection point - wired the event to the handlers here.

        The servive layer never needs to know which hanlders exist.

        Adding a new handler = adding ONE line here. Nothing else Changes.


        """

        from orders.events import (
            order_event_bus,
            OrderPlaced,
            OrderCancelled,
            OrderPaid,
            OrderShipped,
        )
        from orders.events.handlers import (
            handle_send_order_confirmation_email,
            handle_publish_placed_event_to_outbox,
            handle_send_cancellation_email,
            handle_publish_cancelled_event_to_outbox,
            handle_send_payment_success_email,
            handle_publish_completed_event_to_outbox,
            handle_send_shipping_email,
        )

        # Wire: OrderPlaced → two independent handlers
        order_event_bus.subscribe(OrderPlaced, handle_send_order_confirmation_email)
        order_event_bus.subscribe(OrderPlaced, handle_publish_placed_event_to_outbox)
        # Wire: OrderCancelled → two independent handlers
        order_event_bus.subscribe(OrderCancelled, handle_send_cancellation_email)
        order_event_bus.subscribe(OrderCancelled, handle_publish_cancelled_event_to_outbox)
        # Wire: OrderPaid → two independent handlers
        order_event_bus.subscribe(OrderPaid, handle_send_payment_success_email)
        order_event_bus.subscribe(OrderPaid, handle_publish_completed_event_to_outbox)
        # Wire: OrderShipped → one handler
        order_event_bus.subscribe(OrderShipped, handle_send_shipping_email)
