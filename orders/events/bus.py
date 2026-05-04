import logging
from typing import Callable, Dict, List, Type

logger = logging.getLogger('order.events')

class DomainEvent:
       """
       Base class for all domain events.
       Every event in the system must inhert from this.
       The shape of every event it has name a payload.
       """

       event_name: str = ""

       def __init__(self,payload:dict):
              # The payload is the data this event carries.
              #eg: {"order_id": "abc-123", "user_id": 5}
              self.payload = payload

class EventBus:
       """
       The message broker that lives inside the process.
       It holds a registery :{ Eventclass -> [handler_fn, handler_fn,....]}
       Open/closed: You can register new handler without editing this class. 
       Single Responsibility : This class only rotues events to handles.
       }
       """

       def __init__(self):
              # The register is a dict.
              # Key = the event class itself( not a string , the class object)
              # value = list of handler functions that want to react to the event

              self._registery: Dict[Type[DomainEvent],list[Callable]] = {}

       def subscribe(self,event_class: Type[DomainEvent], handler: Callable)-> None:
              """
              register a handler function for a specfic event type.
              called onece at app startup (in AppConfig.reay())
              
              """
              if event_class not in self._registery:
                     self._registery[event_class] = []

              self._registery[event_class].append(handler)
              logger.debug(f"Handler '{handler.__name__}' subscribed to '{event_class.event_name}'")
       
       def publish(self,event: DomainEvent) -> None:
              """
              Called by a service to fire an event.
              The service does Not Know which handler will run-it just publishers.
              """
              handlers = self._registery.get(type(event),[])

              if not handlers:
                     logger.warning(f"Event '{event.event_name}' publlished but no handlers subscribed")
                     return
              
              for handler in handlers:
                     try:
                            logger.info(f"Dispatching '{event.event_name}' -> '{handler.__name__}'")
                            handler(event.payload)
                     except Exception as e:
                            # Single faling hanlder must not crash the others

                            logger.error(
                                   f"Hanlder '{handler.__name__}' failed for event"
                                   f"'{event.event_name}': {e}", exc_info=True,
                            )

# This is the single, shared instance of the bus for the entire orders module.
# It's created here and imported wherever needed. 
order_event_bus = EventBus()