from dataclasses import dataclass
from decimal import Decimal

@dataclass
class ProductDTO: # Data Transfer Object
       id :int
       name :str
       stock :int
       price :Decimal
       brand : str = ""
       specifications: dict = None

