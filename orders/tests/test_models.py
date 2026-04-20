from django.test import TestCase
from orders.tests.factories import ShippingAddressFactory,OrderItemFactory,OrderFactory
from user_auth.tests.factories import UserFactory
from product.tests.factories import ProductFactory, CategoryFactory, ProductVariantFactory, InventoryUnitFactory, ReviewFactory
from orders.services import sync_order_prices
from orders.models import Order,OrderItem
from decimal import Decimal


class OrderModelTests(TestCase):

       def setUp(self):

              self.user = UserFactory()
              self.shipping_address = ShippingAddressFactory(user = self.user)
              self.category = CategoryFactory()
              self.product = ProductFactory(category = self.category)
              self.variant = ProductVariantFactory(product=self.product)
       
       def test_create_new_order(self):
              order = OrderFactory(user = self.user, shipping_address = self.shipping_address, status = 'Cart')
              item1 = OrderItemFactory(
                     order = order,
                     product_id = self.variant.id,
                     product_name = self.product.name,
                     quantity = 2,
                     price_at_purchase = Decimal('100.00')
              )

              order.refresh_from_db()

              self.assertEqual(order.subtotal,Decimal('200.00'))
              self.assertEqual(order.tax_amount, Decimal('36.00'))
              self.assertEqual(order.shipping_fee,Decimal('100.00'))
              self.assertEqual(order.total_price,Decimal('336.00'))


       def test_status_defaults_and_UUID_generation(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)

              self.assertEqual(order.status , 'Cart')
              self.assertIsNotNone(order.order_id)      
              
       def test_tiered_shipping(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)

              item = OrderItemFactory(
                     order = order,
                     product_id = self.variant.id,
                     product_name = self.product.name,
                     quantity = 1,
                     price_at_purchase = Decimal('500.00')
              )

              order.refresh_from_db()

              self.assertEqual(order.shipping_fee,Decimal('100.00'))

       def test_tiered_shipping_over_price(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)

              item = OrderItemFactory(
                     order = order,
                     product_id = self.variant.id,
                     product_name = self.product.name,
                     quantity = 1,
                     price_at_purchase = Decimal('1600.00')
              )

              order.refresh_from_db()

              self.assertEqual(order.shipping_fee, Decimal('0.00'))

       def test_tax_calculation(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)

              item = OrderItemFactory(
                     order = order,
                     product_id = self.variant.id,
                     product_name = self.product.name,
                     quantity = 1,
                     price_at_purchase = Decimal('100.00')
              )

              self.assertEqual(order.tax_amount,Decimal('18.00'))

       def test_grand_total_calculation(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)

              item = OrderItemFactory(
                     order = order,
                     product_id = self.variant.id,
                     product_name = self.product.name,
                     quantity = 1,
                     price_at_purchase = Decimal('1000.00')
              )

              order.refresh_from_db()

              self.assertEqual(order.total_price,Decimal('1280.00'))

       def test_sync_order_prices_updates_cart(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address,status = 'Cart')

              self.product.price = Decimal('500.00')
              self.product.save()
       
              item = OrderItemFactory(
                     order = order,
                     product_id = self.product.id,
                     variant_id = self.variant.id,
                     product_name = self.product.name,
                     quantity = 1,
                     price_at_purchase = None
              )

              self.variant.price_adjustment = Decimal('1000.00')

              self.variant.save()

              sync_order_prices(order)

              item.refresh_from_db()

              self.assertEqual(item.price_at_purchase,Decimal('1500.00'))
              
              

       #--------------------- Edge Cases -----------------------#

       def test_sync_order_prices_ignores_confirmed_orders(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address, status = "OrderConfirmed")

              self.product.price = Decimal('500.00')
              self.product.save()

              item = OrderItemFactory(
                     order = order,
                     product_id = self.product.id,
                     variant_id = self.variant.id,
                     product_name = self.product.name,
                     quantity = 1,
                     price_at_purchase = Decimal('500.00')
              )

              self.variant.price_adjustment = Decimal('1000.00')
              self.variant.save()

              sync_order_prices(order)

              item.refresh_from_db()

              self.assertEqual(item.price_at_purchase,Decimal('500.00'))
              

       def test_empty_cart_values(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)

              order.refresh_from_db()

              self.assertEqual(order.subtotal,Decimal('0'))
              self.assertEqual(order.tax_amount,Decimal('0'))
              self.assertEqual(order.shipping_fee,Decimal('0'))

       def test_automatic_total_price_update(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)
              
              self.assertEqual(order.total_price,Decimal('0.00'))
              
              item = OrderItemFactory(
                     order = order,
                     product_id = self.variant.id,
                     product_name = self.product.name,
                     quantity = 1,
                     price_at_purchase = Decimal('100.00')
              )

              order.refresh_from_db()

              self.assertEqual(order.total_price,Decimal('218.00'))

       def test_user_deletion(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)

              item = OrderItemFactory(
                     order = order,
                     product_id = self.variant.id,
                     product_name = self.product.name,
                     quantity = 1,
                     price_at_purchase = Decimal('1000.00')
              )

              self.user.delete()

              order.refresh_from_db()
              
              self.assertIsNone(order.user)

       #------Custom query set Tests ------------- #

       def test_valid_sales_querset(self):

              OrderFactory(user = self.user,status = 'Cart')
              OrderFactory(user = self.user,status = 'Cancelled')
              OrderFactory(user = self.user,status = 'Pending')

              valid1 = OrderFactory(user = self.user,status = 'Delivered')
              valid2 = OrderFactory(user = self.user,status = 'OrderConfirmed')

              sales = Order.objects.valid_sales()

              self.assertEqual(sales.count(),2)
              self.assertIn(valid1,sales)
              self.assertIn(valid2,sales)

       def test_get_or_create_cart(self):
              cart1, created1 = Order.objects.get_or_create_cart(self.user)
              self.assertTrue(created1)
              self.assertEqual(cart1.status,'Cart')

              cart2, created2 = Order.objects.get_or_create_cart(self.user)
              self.assertFalse(created2)
              self.assertEqual(cart1.id,cart2.id)

class OrderItemModelTests(TestCase):

       def setUp(self):

              self.user = UserFactory()
              self.shipping_address = ShippingAddressFactory(user = self.user)
              self.category = CategoryFactory()
              self.product = ProductFactory(category = self.category)
              self.variant = ProductVariantFactory(product=self.product)


       def test_price_locking_when_product_price_changes(self):

              order = OrderFactory(user= self.user,shipping_address = self.shipping_address, status = "OrderConfirmed")

              variant = ProductVariantFactory(product=self.product,price_adjustment = Decimal('50.00'))

              item = OrderItemFactory(
                     order = order,
                     product_id = variant.id,
                     product_name = self.product.name,
                     quantity = 1,
                     price_at_purchase = variant.price_adjustment
              )

              order.refresh_from_db()
              original_total = order.total_price

              variant.price_adjustment =  Decimal('999.00')
              variant.save()

              order.refresh_from_db()
              self.assertEqual(item.price_at_purchase,Decimal('50.00'))
              self.assertEqual(order.total_price,original_total)

       def test_quantity_mulitplier(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)
              item = OrderItemFactory(
                     order = order,
                     product_id = self.product.id,
                     variant_id = self.variant.id,
                     quantity = 3,
                     price_at_purchase = Decimal('100.00')
              )

              self.assertEqual(item.total_price,Decimal('300.00'))

       def test_item_total_safe_with_no_price(self):
              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)
              item = OrderItemFactory(
                     order = order,
                     product_id = self.product.id,
                     variant_id = self.variant.id,
                     quantity = 3,
                     price_at_purchase = None
              )

              self.assertEqual(item.total_price,Decimal('0'))




       #--------------- Edge Case --------------- #

       def test_zero_quantity_total(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)

              item = OrderItemFactory(
                     order = order,
                     product_id = self.product.id,
                     variant_id = self.variant.id,
                     quantity = 0,
                     price_at_purchase = Decimal('100.00')
              )

              self.assertEqual(item.total_price,Decimal('0.00'))

       def test_order_total_recalculates_on_item_delete(self):

              order = OrderFactory(user = self.user, shipping_address = self.shipping_address)

              item1 = OrderItemFactory(
              order = order,
              price_at_purchase = Decimal('500.00'),
              quantity = 1,
              product_id = self.product.id
              )
              item2 = OrderItemFactory(
              order = order,
              price_at_purchase = Decimal('500.00'),
              quantity = 1,
              product_id = self.product.id
              )

              order.refresh_from_db()

              self.assertEqual(order.total_price,Decimal('1280.00'))

              item1.delete()

              order.refresh_from_db()

              self.assertEqual(order.total_price,Decimal('690.00'))


       #----------- CustomQuery Sets Test ----------------- #

       def test_top_selling_analytics(self):
              order = OrderFactory(user=self.user, status='Delivered')
              
              # Product A: Total 5 sold
              OrderItemFactory(order=order, product_name="Laptop", quantity=3)
              OrderItemFactory(order=order, product_name="Laptop", quantity=2)
              
              # Product B: Total 2 sold
              OrderItemFactory(order=order, product_name="Mouse", quantity=2)
              
              # Product C: Total 10 sold
              OrderItemFactory(order=order, product_name="Keyboard", quantity=10)
              
              # Run the query: Limit to top 2
              top_sellers = OrderItem.objects.top_selling(limit=2)
              
              self.assertEqual(len(top_sellers), 2)
              
              # #1 Should be Keyboard (10)
              self.assertEqual(top_sellers[0]['product_name'], "Keyboard")
              self.assertEqual(top_sellers[0]['total_sold'], 10)
              
              # #2 Should be Laptop (5)
              self.assertEqual(top_sellers[1]['product_name'], "Laptop")
              self.assertEqual(top_sellers[1]['total_sold'], 5)


class ShippingAddressModelTests(TestCase):

       def setUp(self):
              self.user = UserFactory()
              self.address = ShippingAddressFactory(
                     user = self.user,
                     full_name = "Tony Stark",
                     city = "Malibu, California"
              )
       
       def test_is_default_flag(self):
              
              self.address.is_default = True
              self.address.save()

              self.address.refresh_from_db()
              self.assertTrue(self.address.is_default)

       def test_string_representation(self):
              self.assertEqual(str(self.address),"Tony Stark - Malibu, California")
       
       # ============= Edge Case ============== #

       def test_address_deletion_does_not_delete_order(self):

              order = OrderFactory(user = self.user,shipping_address = self.address)

              self.address.delete()

              order.refresh_from_db()

              self.assertIsNotNone(order.order_id)

              self.assertIsNone(order.shipping_address)