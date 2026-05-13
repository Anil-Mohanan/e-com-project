from django.urls import path
from .views import DashboardSummaryView, SalesChartView,TopSellingProductsView,UserListView,LowStockProductView,AuditLogListView, CartAbandonmentReportView, ZeroResultSearchView,AdminActionLogView

urlpatterns = [
       path('dashboard-summary/', DashboardSummaryView.as_view(),name = 'dashboard-summary'),
       path('sales-chart/',SalesChartView.as_view(),name='sales-chart'),
       path('top-products/', TopSellingProductsView.as_view(), name='top-products'),
       path('users/',UserListView.as_view(), name='user-list'),
       path('low-stock/',LowStockProductView.as_view(),name='low-stock'),
       path('audit/',AuditLogListView.as_view(),name = 'audit'),
       path('abandonment-report/',CartAbandonmentReportView.as_view(),name='abandonment-report'),
       path('zero-result-searches/',ZeroResultSearchView.as_view(),name='zero-result-searches'),
       path('admin-actions/', AdminActionLogView.as_view(), name='admin-actions'),
]
handler404 = 'cofig.error_views.error_404'
handler500 = 'cofig.error_views.error_500'