import factory
from user_auth.tests.factories import UserFactory
from product.models import Category,Product,ProductVariant,InventoryUnit,Review,ProductPurchaseHistory

class CategoryFactory(factory.django.DjangoModelFactory):
       class Meta:
              model = Category

       name = factory.Sequence(lambda n: f"test_category {n}")
       image = None
       required_specs_keys = []

class ProductFactory(factory.django.DjangoModelFactory):
       class Meta:
              model = Product
       
       name = factory.Sequence(lambda n: f'test_product {n}')
       category = factory.SubFactory(CategoryFactory)
       description = factory.Faker('paragraph')
       price = factory.Faker('pydecimal',left_digits = 4,right_digits = 2,positive = True)
       stock = factory.Faker('random_int',min=1,max=100)
       seller = factory.SubFactory(UserFactory)
       specifications = {}
       brand = factory.Faker('company')
       is_active = True

class ProductVariantFactory(factory.django.DjangoModelFactory):
       class Meta:
              model = ProductVariant

       product = factory.SubFactory(ProductFactory)
       attribute_name = factory.Sequence(lambda n: f'attribute_{n}')
       attribute_value = factory.Sequence(lambda n: f'value_{n}')
       color = factory.Faker('color_name')
       price_adjustment = factory.Faker('pydecimal',left_digits = 4,right_digits = 2, positive = True)
       stock = factory.Faker('random_int',min=1,max=100)
       is_active = True

class InventoryUnitFactory(factory.django.DjangoModelFactory):
       class Meta:
              model = InventoryUnit

       product = factory.SubFactory(ProductFactory)
       variant = factory.SubFactory(ProductVariantFactory)
       serial_number = factory.Sequence(lambda n: f'SN-{n}')
       status = 'In Stock'

class ReviewFactory(factory.django.DjangoModelFactory):
       class Meta:
              model = Review
       
       product = factory.SubFactory(ProductFactory)
       user = factory.SubFactory(UserFactory)
       rating = factory.Faker('random_int',min=0, max=5)
       comment = factory.Faker('sentence')

class ProductPurchaseHistoryFactory(factory.django.DjangoModelFactory):

       class Meta:
              model = ProductPurchaseHistory
       
       user_id = factory.Sequence(lambda n: n + 1)
       product = factory.SubFactory(ProductFactory)

