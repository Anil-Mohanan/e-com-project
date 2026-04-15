from django.contrib.auth import  get_user_model

User = get_user_model()

def get_recent_users_list():
       
       
       users = User.objects.filter(is_staff = False).values('id','first_name','email', 'date_joined')

       return list(users)

def get_total_customers_count():

       total_users = User.objects.filter(is_staff=False).count()#Total Customers (everyone who is not and Admin)

       return total_users