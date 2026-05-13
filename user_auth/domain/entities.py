from ipaddress import ip_address
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SessionDTO:
       jti : str
       created_at : datetime
       expires_at : datetime
       ip_address : str
       device_name : str

       