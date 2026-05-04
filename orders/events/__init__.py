from .bus import DomainEvent, EventBus, order_event_bus

# Domain Event Definitions 
# Each class represents a single thing that Happend in the domain 
# named in past tense - they are facts, not commands,


class OrderPlaced(DomainEvent):
       """Fired when a cart successfully checkout ."""
       event_name = 'order.placed'

class OrderCancelled(DomainEvent):
       """Fired When an order is cancelled."""
       event_name = "order.cancelled"

class OrderPaid(DomainEvent):
       """Fired when an order is makred as Paid"""      
       event_name = 'order.paid'

class OrderShipped(DomainEvent):
       """Fired when an order status is changed to shipped."""
       event_name = "order.shipped"

__all__ = [
       "DomainEvent",
       "EventBus",
       "order_event_bus",
       "OrderPlaced",
       "OrderCancelled",
       "OrderPaid",
       "OrderShipped",
]
