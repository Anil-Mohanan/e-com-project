import factory
from user_auth.models import User
from user_auth.models import UserDeviceSession

class UserFactory(factory.django.DjangoModelFactory):
       class Meta:
              model = User
              skip_postgeneration_save = True

       email = factory.Sequence(lambda n: f"user_{n}@test.com")
       is_customer = True
       is_seller = False
       is_email_verified = False
       jwt_version = 1

       @factory.post_generation
       def password(self,create,extracted,**kwargs):
              if not create: # only apply if actually saving to the DB
                     return
              
              self.set_password(extracted if extracted else 'TestPass@1234')

              self.save()
                     

class UserDeviceSessionFactory(factory.django.DjangoModelFactory):
       class Meta:
              model = UserDeviceSession

       user = factory.SubFactory(UserFactory)
       jti = factory.Faker('uuid4')
       ip_address = factory.Faker('ipv4')
       device_name = 'Test Device'
       
