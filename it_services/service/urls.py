from django.contrib import admin
from django.urls import path,include
from service.views import home,register,create_service,delete_service,update_service,login_user,logout_user,service_list,pay_service,show_service,pay_success,verify_email

urlpatterns = [
    path('',home,name='home'),
    path('register/',register,name='register'),
    path('verfiy-email/',verify_email,name='verify_email'),
    path('login/',login_user,name='login_user'),
    path('logout/',logout_user,name='logout_user'),
    path('create-service/',create_service,name='create_service'),
    path('service-list/',service_list,name='service_list'),
    path('pay-success/',pay_success,name='pay_success'),
    path('pay-service/<int:id>/',pay_service,name='pay_service'),
    path('show-service/<int:id>/',show_service,name='show_service'),
    path('delete-service/<int:id>/',delete_service,name='delete_service'),
    path('update-service/<int:id>/',update_service,name='update_service'),
]