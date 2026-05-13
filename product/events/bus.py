import logging
from typing import Callable, Dict, List, Type

logger = logging.getLogger("product.events")


class DomainEvent:
       """
       Base class for all product domain events.
       Domains must stay independent of each other's internals.
       """
       event_name: str = ""

       def __init__(self, payload: dict):
              # The payload is the data this event carries
              self.payload = payload


class EventBus:
       """
       In-process message broker for the product domain.
       Same engine as orders.EventBus — same pattern, completely separate registry.
       """

       def __init__(self):
              # Key = event class object, Value = list of handler functions
              self._registry: Dict[Type[DomainEvent], List[Callable]] = {}

       # ↑ __init__ ends here. subscribe and publish are CLASS METHODS, not nested inside __init__

       def subscribe(self, event_class: Type[DomainEvent], handler: Callable) -> None:

              """Register a handler at startup (called from AppConfig.ready)."""
              if event_class not in self._registry:
                  self._registry[event_class] = []
              self._registry[event_class].append(handler)
              logger.debug(f"Handler '{handler.__name__}' subscribed to '{event_class.event_name}'")

       def publish(self, event: DomainEvent) -> None:
              """
              Fire an event. The publisher knows nothing about who handles it.
              One failing handler never crashes the others — each is isolated.
              """
              handlers = self._registry.get(type(event), [])
              # ↑ Note: get(type(event), []) — the default [] is the SECOND argument to get()

              if not handlers:
                  logger.warning(f"Event '{event.event_name}' published but no handlers subscribed.")
                  return

              for handler in handlers:
                  try:
                      logger.info(f"Dispatching '{event.event_name}' → '{handler.__name__}'")
                      handler(event.payload)
                  except Exception as e:
                      logger.error(
                          f"Handler '{handler.__name__}' failed for event "
                          f"'{event.event_name}': {e}",
                          exc_info=True,
                      )


# Single shared instance for the product domain
product_event_bus = EventBus()
