import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')# telling celery where to find the djanog settings 

app = Celery('e_com')

app.config_from_object('django.conf:settings',namespace = 'CELERY') # telling  celery to read config from django settings Using namespace='CELERY' means all celery-related configuration keys
# must have a 'CELERY_' prefix.

app.autodiscover_tasks([
       'orders.infrastructure',# tells celery to scan orders/infrastructure/tasks.py specifically
       'product', #product/tasks.py 
       'payments', #payments/tasks.py
       'user_auth',# user_auth tasks
       'analytics' ,#analytics tasks
])     
