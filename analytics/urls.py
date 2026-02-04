from django.urls import path
from .views import DashboardSummaryView, SalesChartView,TopSellingProductsView,UserListView,LowStockProductView

urlpatterns = [
       path('summary/', DashboardSummaryView.as_view(),name = 'dahsboard-summary'),
       path('sales-chart/',SalesChartView.as_view(),name='sales-chart'),
       path('top-products/', TopSellingProductsView.as_view(), name='top-products'),
       path('users/',UserListView.as_view(), name='user-list'),
       path('low-stock/',LowStockProductView.as_view(),name='low-stock'),
]