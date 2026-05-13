import factory
from analytics.models import AuditLog
from user_auth.tests.factories import UserFactory

class AuditLogFactory(factory.django.DjangoModelFactory):
       class Meta:
              model = AuditLog
       user = factory.SubFactory(UserFactory)
       method = 'GET'
       Path = '/api/products/'
       status_code = 200
       ip_address = factory.Faker('ipv4')