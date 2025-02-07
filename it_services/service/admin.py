from django.contrib import admin
from service.models import Service,Subscription,Otp
# Register your models here.
admin.site.register(Service)
admin.site.register(Subscription)
admin.site.register(Otp)