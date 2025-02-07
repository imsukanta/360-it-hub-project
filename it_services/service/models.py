from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Service(models.Model):
    service_name=models.CharField(max_length=50)
    payment_terms=models.CharField(max_length=50)
    service_price=models.FloatField(default=0)
    service_package=models.CharField(max_length=50)
    service_tax=models.FloatField(default=0)
    service_image=models.ImageField(upload_to="image/")
    active=models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.service_name}+{self.service_price}"

class Subscription(models.Model):
    service=models.ForeignKey(Service,on_delete=models.DO_NOTHING)
    user_id=models.ForeignKey(User,on_delete=models.CASCADE)
    amount_paid=models.FloatField(default=0)
    payment_id=models.CharField(max_length=150)
    order_id=models.CharField(max_length=150)
    signature=models.CharField(max_length=150)
    status=models.CharField(max_length=50)
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.service}+{self.user_id}"

class Otp(models.Model):
    user_id=models.ForeignKey(User,on_delete=models.CASCADE)
    otp_string=models.CharField(max_length=6)