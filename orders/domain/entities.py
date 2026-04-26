from typing import List, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from .strategies import ShippingStrategy, StandardShippingStrategy, TaxStrategy, IndianGSTStrategy



@dataclass
class OrderItemEntity:
       product_id : int
       variant_id : Optional[int]
       product_name : str
       quantity : int
       price_at_purchase : Optional[Decimal]

       @property
       def line_total(self):
              return (self.price_at_purchase or 0) * self.quantity

@dataclass
class OrderEntity:
       order_id : str
       user_id : int
       status : str
       is_paid : bool
       paid_at : Optional[datetime] = None
       items: List[OrderItemEntity] = field(default_factory=list)


       @property
       def subtotal(self):
              return sum(item.line_total for item in self.items)

@dataclass
class OrderEventEntity:
       id: int
       event_type: str
       payload: dict

@dataclass
class OrderEmailItemDTO:
       product_name : str
       quantity: int

@dataclass
class OrderEmailDTO: # DTO (Data Transfer Object)
       order_id : str
       first_name : str
       email: str
       total_price: Decimal
       status : str
       items : List[OrderEmailItemDTO]
       address_line_1 : Optional[str] = None
       city : Optional[str] = None
       payment_method: str = "Cod/Online"


def calculate_order_total(
       subtotal: Decimal, 
       shipping_strategy: ShippingStrategy = StandardShippingStrategy(),
       tax_strategy: TaxStrategy = IndianGSTStrategy()
) -> Decimal:
       tax = tax_strategy.calculate_tax(subtotal)
       shipping = shipping_strategy.calculate_fee(subtotal)
       return subtotal + tax + shipping
