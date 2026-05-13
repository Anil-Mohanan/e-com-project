"""
Orders Domain — Public Interface

Service functions that other domains may import:
- orders.payment_services.get_order_details_for_payment
- orders.payment_services.confirm_order_payment
- orders.analytics_services.get_dashboard_order_metrics
- orders.analytics_services.get_sales_chart_data
- orders.analytics_services.get_top_selling_products

Event handlers (called via send_task):
- orders.handle_inventory_failed
- orders.handle_payment_successful

Everything else is INTERNAL to this domain.
"""
