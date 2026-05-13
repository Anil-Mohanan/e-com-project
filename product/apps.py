from django.apps import AppConfig


class ProductConfig(AppConfig):
    name = 'product'

    def ready(self):
        import product.signals

        # This runs ONCE when django boots.
        # Adding a new handler = one new subscribe() line here. nothing else changes.

        from product.events import(
            product_event_bus,
            ProductViewed,
            ProductSearched,
            ProductAddedToCart,
        )

        from product.events.handlers import (
            handle_log_product_view,
            handle_log_product_search,
            handle_log_product_added_to_cart,
        )

        #Wire: when a product page is opened -> log it 
        product_event_bus.subscribe(ProductViewed,handle_log_product_view)

        #Wire : when a user searches -> log the query + result count
        product_event_bus.subscribe(ProductSearched,handle_log_product_search)

        #Wire: when a product is added to cart -> log it
        product_event_bus.subscribe(ProductAddedToCart,handle_log_product_added_to_cart)

