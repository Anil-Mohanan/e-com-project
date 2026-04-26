from abc import ABC, abstractmethod
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings

#1: Strategy Interface
class ShippingStrategy(ABC):
       @abstractmethod
       def calculate_fee(self,subtotal: Decimal) -> Decimal:
              pass
class TaxStrategy(ABC):
       @abstractmethod
       def calculate_tax(self, subtotal: Decimal) -> Decimal:
              pass

class IndianGSTStrategy(TaxStrategy):
       def calculate_tax(self,subtotal:Decimal) -> Decimal:

              return subtotal * Decimal('0.18')

class USSStateTaxStrategy(TaxStrategy):
       def calculate_tax(self,subtotal:Decimal) -> Decimal:

              return subtotal * Decimal('0.07')

class TaxFreeStrategy(TaxStrategy):
       def calculate_tax(self, subtotal: Decimal) -> Decimal:
              return Decimal('0')

class StandardShippingStrategy(ShippingStrategy):
       def calculate_fee(self,subtotal: Decimal) -> Decimal:
              if subtotal == Decimal('0'):
                     return Decimal('0')
              if subtotal > Decimal('1500'):
                     return Decimal('0')
              return Decimal('100')

class InternationalShippingStrategy(ShippingStrategy):
       def calculate_fee(self,subtotal: Decimal) -> Decimal:
              if subtotal == Decimal('0'):
                     return Decimal('0')
              return Decimal('500')

class NotificationStrategy(ABC):
       @abstractmethod
       def send(self,subject: str, message: str, recipient: str):
              pass

class EmailNotificationStrategy(NotificationStrategy):

       # This strategy specifically uses Django's Email system

       def send(self,subject:str, message: str, recipient: str):
              
              send_mail(
                     subject,
                     message,
                     settings.DEFAULT_FROM_EMAIL,
                     [recipient]
              )
class SMSNotificaionStrategy(NotificationStrategy):

       def send(self,subject:str,message:str,recipient:str):
              # Just a placeholder to show how easy it is to add Twilio/AWS SNS later!
              print(f"Sending SMS to {recipient}: {subject}")

