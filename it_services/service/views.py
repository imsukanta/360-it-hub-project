from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_protect,csrf_exempt
from service.models import Service,Subscription,Otp
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import permission_required,login_required
import razorpay
from django.core.mail import send_mail
from django.conf import settings
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import random
import string
from django.urls import reverse
# Create your views here.

#calculate total price
def send_email(name,from_email,to_email,subject,html_content):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.API_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    email_data = sib_api_v3_sdk.SendSmtpEmail(
        sender={"name": name, "email": from_email},  # Use verified email
        to=[{"email": to_email}],  # Replace with recipient email
        subject=subject,
        html_content=html_content
    )

    try:
        api_response = api_instance.send_transac_email(email_data)
        print("Email sent successfully: ", api_response)
    except ApiException as e:
        print("Error sending email: %s\n" % e)
        
def total_price(id):
    service=Service.objects.get(id=id)
    price=((100+int(service.service_tax))/100)*service.service_price
    return price

def home(request):
    service=Service.objects.filter(active=True)
    return render(request,'homeService.html',{'service':service})

def show_service(request,id):
    service=Service.objects.get(id=id,active=True)
    if request.user.is_authenticated:
        subscription = Subscription.objects.filter(user_id=request.user, service=service).first()
    else:
        subscription = Subscription.objects.filter(service=service).first()
    return render(request,"show_service.html",{'service':service,'subscription':subscription})

@csrf_exempt
def pay_service(request,id):
    if not request.user.is_authenticated:
        messages.error(request,"You are not login. Login first")
        return redirect('login_user')
    service=Service.objects.get(id=id,active=True)
    price=int(total_price(id))
    client = razorpay.Client(auth=("rzp_test_e664V0FP0zQy7N", "QdnuRxUHrPGeiJc9lDTXYPO7"))
    data = { "amount": int(price)*100, "currency": "INR", "receipt": "order_rcptid_"+str(service.id) }
    payment = client.order.create(data=data)
    order_details=client.order.fetch(payment['id'])
    subscription=Subscription.objects.create(user_id=request.user,service=service,order_id=order_details['id'],status=order_details['status'],amount_paid=order_details['amount_paid'])
    subscription.save()
    return render(request,"pay_service.html",{'service':service,'price':price,'payment':payment})

@csrf_exempt
def pay_success(request):
    if request.method=='POST':
        razorpay_payment_id=request.POST.get('razorpay_payment_id')
        razorpay_order_id=request.POST.get('razorpay_order_id')
        razorpay_signature=request.POST.get('razorpay_signature')
        subscription=Subscription.objects.filter(order_id=razorpay_order_id).first()
        if razorpay_order_id and razorpay_payment_id and razorpay_signature:
            try:
                client = razorpay.Client(auth=("rzp_test_e664V0FP0zQy7N", "QdnuRxUHrPGeiJc9lDTXYPO7"))
                client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
                })
                payment_details = client.payment.fetch(razorpay_payment_id)
                subscription.amount_paid=payment_details['amount']
                subscription.payment_id=razorpay_payment_id
                subscription.signature=razorpay_signature
                subscription.status=payment_details['status']
                subscription.save()
                messages.success(request,'Successfully Verify')
            except Exception as e:
                messages.error(request,"Failed verify")
        else:
            messages.error("You have not pay anything")
            return redirect('home')
    return render(request,'success.html')
def verify_email(request):
    email_id=request.GET.get('email')
    user=User.objects.filter(email=email_id).first()
    otp=Otp.objects.filter(user_id=user).first()
    if request.method=='POST':
        html_otp=request.POST.get('otp')
        if html_otp==otp.otp_string:
            user.is_active=True
            user.save()
            otp.delete()
            messages.success(request,"Successfully verify your account")
            return redirect('home')
        else:
            messages.error(request,'Wrong otp')
            url=reverse('verify_email') + f'?email={email_id}'
            return redirect(url)

    return render(request,'verify_email.html')

@permission_required('services.service_list',login_url='/login/')
def service_list(request):
    service=Service.objects.all()
    for srvice in service:
        print(srvice.service_image)
    return render(request,"serviceList.html",{'service':service})
@csrf_protect
def register(request):
    if request.method=="POST":
        first_name=request.POST.get('first_name')
        last_name=request.POST.get('last_name')
        email=request.POST.get('email')
        password=request.POST.get('password')
        confirm_password=request.POST.get('confirm_password')
        if password!=confirm_password:
            messages.warning(request,"Password mismatch")
            return redirect('register')
        if email =="" or first_name=="" or last_name=='':
            messages.warning(request,'Email, First Name, Last Name required')
            return redirect('register')
        
        random_string = ''.join(random.choices(string.digits, k=6))       
        user=User.objects.filter(email=email).first()
        if user:
            if user.is_active==True:
                messages.success(request,"You are alerady register")
                return redirect('home')
            otp=Otp.objects.filter(user_id=user).first()
            if otp:
                otp.otp_string=random_string
                otp.save()
            else:
                otp_create=Otp.objects.create(user_id=user,otp_string=random_string)
                otp_create.save()
        else:
            user_create=User.objects.create_user(first_name=first_name,last_name=last_name,email=email,password=password,username=email)
            user_create.is_active=False
            otp=Otp.objects.filter(user_id=user_create).first()
            if otp:
                otp.otp_string=random_string
                otp.save()
            else:
                otp_create=Otp.objects.create(user_id=user_create,otp_string=random_string)
                otp_create.save()
            user_create.save()
        subject=f"Verify email"
        html_content=f"Your otp is:{random_string}"
        send_email("Sukanta Malik","imsukantamalik@gmail.com",request.POST.get('email'),subject,html_content)
        messages.success(request,'Verify your email address')
        url = reverse('verify_email') + f'?email={email}'
        return redirect(url)
    return render(request,'register.html')
@csrf_protect
def login_user(request):
    if request.method=='POST':
        email=request.POST.get('email')
        password=request.POST.get('password')
        user=authenticate(request,username=email,password=password)
        if user is not None:
            login(request,user)
            messages.success(request,"User successfully login")
            return redirect('home')
        else:
            messages.error(request,"You are not login try to register")
            return redirect('register')
    return render(request,'login.html')
def logout_user(request):
    logout(request)
    messages.success(request,"Successfully logout")
    return redirect('login_user')

@permission_required('services.create_service',login_url="/login/")
@csrf_protect
def create_service(request):
    if request.method=="POST":
        service_name=request.POST['service_name']
        payment_terms=request.POST['payment_terms']
        service_price=request.POST['service_price']
        service_tax=request.POST['service_tax']
        service_package=request.POST['service_package']
        service_image = request.FILES.get('service_image')
        active=request.POST.get('active')=='on'
        service=Service.objects.create(service_name=service_name,payment_terms=payment_terms,service_price=service_price,service_tax=service_tax,service_package=service_package,service_image=service_image,active=active)
        service.save()
        return redirect('home')
    return render(request,'create_service.html')

@permission_required('services.update_service',login_url='/login/')
@csrf_protect
def update_service(request,id):
    service=Service.objects.get(id=id)
    if request.method=="POST":
        service_name=request.POST['service_name']
        payment_terms=request.POST['payment_terms']
        service_price=request.POST['service_price']
        service_tax=request.POST['service_tax']
        service_package=request.POST['service_package']
        service_image=request.FILES.get('service_image')
        active=request.POST.get('active')=='on'
        service.service_name=service_name
        service.payment_terms=payment_terms
        service.service_price=service_price
        service.service_tax=service_tax
        service.service_package=service_package
        service.service_image=service_image
        service.active=active
        service.save()
        return redirect('home')
    return render(request,'update_service.html',{'service':service})
@permission_required('services.delete_service',login_url='/login/')
def delete_service(request,id):
    service=Service.objects.get(id=id)
    service.delete()
    return redirect('home')
