from typing import List, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime

@dataclass
class PaymentEntity:
       order_id : str
       transaction_id : Optional[str]
       payment_method : str
       amount : Decimal
       status : str
       created_at: Optional[datetime]

@dataclass
class PaymentEventEntity:
       id: int
       event_type: str
       payload: dict

