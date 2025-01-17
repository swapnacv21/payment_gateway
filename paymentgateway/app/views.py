from django.shortcuts import render
from .models import *
from django.http import JsonResponse
from django.conf import settings
import razorpay
import json
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

# key id :    rzp_test_tqNZMcog4na3wC
# key secret :   xbRCeWA0xC53GouFEd7kMQcz


def home(request):
    return render(request,"index.html")

def order_payment(request):
    if request.method == "POST":
        name = request.POST.get("name")
        amount = request.POST.get("amount")
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({"amount":int(amount)*100, "currency":"INR","payment_capture":"1"})
        order_id = razorpay_order['id']
        order = Order.objects.create(name=name,amount=amount,provider_order_id=order_id)
        order.save()
        return render(
            request,
            "index.html",
            {
                "callback_url":""+""+"",
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "order":order,
            },
        )
    return render(request,"index.html")

@csrf_exempt
def call_back(request):
    def verify_signature(response_data):
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))
        return client.utility.verify_payment_signature(response_data)
    if "razorpay_signature" in request.POST:
        payment_id = request.POST.get("razorpay_payment_id","")
        provider_order_id = request.POST.get("razorpay_order_id","")
        signature_id = request.POST.get("razorpay_signature","")
        order = Order.objects.get(provider_order_id=provider_order_id)
        order.payment_id = signature_id
        order.save()
        if not verify_signature(request.POST):
            order.status =  PaymentStatus.SUCCESS
            order.save()
            return render(request,"callback.html",context={"status":order.status})
        else:
            order.status = PaymentStatus.FAILURE
            order.save()
            return render(request,"callback.html",context={"status":order.status})
    else:
        payment_id = json.loads(request.POST.get("error[metadata]")).get("payment_id")
        provider_order_id = json.loads(request.POST.get("error[metadata]")).get("order_id")
        order = Order.objects.get(provider_order_id=provider_order_id)
        order.payment_id =payment_id
        order.status = PaymentStatus.FAILURE
        order.save()
        return render(request,"callback.html",context={"status":order.status})



        

