from abc import ABC, abstractmethod
from analytics.services import get_total_customers_count
from orders.services.analytics import get_dashboard_order_metrics,get_daily_sales_chart_data,get_monthly_sales_chart_data
from product.services import get_active_products_count


class MetricProviderStrategy(ABC):
       @abstractmethod
       def get_metrics(self) -> dict:
              pass

class OrderMetricsProvider(MetricProviderStrategy):
       def get_metrics(self) -> dict:
              
              metrics = get_dashboard_order_metrics()
              return {
                     "total_revenue": metrics['total_revenue'],
                     "total_orders": metrics['total_orders']
              }

class ProductMetricsProvider(MetricProviderStrategy):
       def get_metrics(self) -> dict:
              
              return {
                     "total_products": get_active_products_count()
              }

class UserMetricsProvider(MetricProviderStrategy):
       def get_metrics(self) -> dict:
             
              return {
                     "total_users": get_total_customers_count()
              }

# --- CHART AGGREGATION STRATEGIES ---

class ChartAggregationStrategy(ABC):
       @abstractmethod
       def get_data(self) -> list:
              pass

class DailyAggregationStrategy(ChartAggregationStrategy):
       def get_data(self) -> list:
              
              return get_daily_sales_chart_data()

class MonthlyAggregationStrategy(ChartAggregationStrategy):
       def get_data(self) -> list:
       
              return get_monthly_sales_chart_data()
