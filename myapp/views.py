from django.shortcuts import render, redirect, get_object_or_404
from .models import Products, OrderDetail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.db.models import Q
import razorpay
import json
from .forms import ProductForm, UserRegistrationForm
from django.db.models import Sum
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def index(request):
    """
    Fetch all products and render the index page.
    """
    products = Products.objects.all()
    return render(request, "myapp/index.html", {'products': products})

def detail(request, id):
    """
    Fetch the product with the given ID and render the detail page.
    """
    product = get_object_or_404(Products, id=id)
    return render(request, 'myapp/detail.html', {'product': product})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('login')

@login_required
def create_checkout_session(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = Products.objects.get(id=product_id)

        order_data = {
            'amount': int(product.price * 100),
            'currency': 'INR',
            'payment_capture': '1'
        }
        order = client.order.create(data=order_data)
        OrderDetail.objects.create(
            user=request.user,
            product=product,
            razorpay_order_id=order["id"],
            amount=product.price
        )
        return render(request, 'myapp/payment.html', {
            'order_id': order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'product_name': product.name,
            'price': product.price,
            'product': product
        })
    return redirect('/')

@csrf_exempt
def verify_payment(request):
    if request.method == 'POST':
        payment_response = json.loads(request.body)
        params_dict = {
            'razorpay_order_id': payment_response['razorpay_order_id'],
            'razorpay_payment_id': payment_response['razorpay_payment_id'],
            'razorpay_signature': payment_response['razorpay_signature']
        }

        try:
            client.utility.verify_payment_signature(params_dict)

            order = OrderDetail.objects.get(razorpay_order_id=params_dict['razorpay_order_id'])
            order.razorpay_payment_intent = params_dict['razorpay_payment_id']
            order.has_paid = True
            order.save()

            return JsonResponse({'status': 'success'})
        
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'status': 'error'})
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@csrf_exempt
def razorpay_webhook(request):
    if request.method == "POST":
        try:
            webhook_secret = "9vGF@ge3RrLLuBu"  # Same as in Razorpay dashboard
            received_data = json.loads(request.body)

            # Validate the Razorpay signature
            razorpay_signature = request.headers.get("X-Razorpay-Signature")
            expected_signature = hmac.new(
                webhook_secret.encode(),
                request.body,
                hashlib.sha256
            ).hexdigest()

            if razorpay_signature != expected_signature:
                return JsonResponse({"error": "Invalid signature"}, status=400)

            # Handle different events
            event_type = received_data.get("event")
            
            if event_type == "payment.authorized":
                print("Payment authorized:", received_data)

            elif event_type == "payment.failed":
                print("Payment failed:", received_data)

            elif event_type == "order.paid":
                print("Order Paid:", received_data)

            return JsonResponse({"status": "Webhook received"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=4)

def search_products(request):
    query = request.GET.get('item_name', '')
    if query:
        products = Products.objects.filter(
            Q(name__icontains=query) | 
            Q(desc__icontains=query)
        )
    else:
        products = Products.objects.all()
    
    return render(request, 'myapp/search_results.html', {
        'products': products, 
        'query': query
    })

@login_required
def payment_success(request):
    latest_order = OrderDetail.objects.filter(user=request.user, has_paid=True).last()
    return render(request, 'myapp/payment_success.html', {
        'product': latest_order.product if latest_order else None
    })

@login_required
def payment_failed(request):
    latest_order = OrderDetail.objects.filter(user=request.user, has_paid=False).last()
    return render(request, 'myapp/payment_failed.html', {
        'product': latest_order.product if latest_order else None,
        'error_message': 'Payment could not be processed'
    })

@login_required
def create_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES)
        if product_form.is_valid():
            new_product = product_form.save(commit=False)
            new_product.user = request.user
            new_product.save()
            return redirect('dashboard')
    product_form = ProductForm()
    return render(request, 'myapp/create_product.html', {'product_form': product_form})

@login_required
def product_edit(request, id=id):
    product = Products.objects.get(id=id)
    # Check if the user owns this product
    if product.user != request.user:
        return redirect('dashboard')
    product_form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST':
        if product_form.is_valid():
            product_form.save()
            return redirect('dashboard')
    return render(request, 'myapp/product_edit.html', {'product_form': product_form, 'product': product})

@login_required
def product_delete(request, id=id):
    product = Products.objects.get(id=id)
    # Check if the user owns this product
    if product.user != request.user:
        return redirect('dashboard')
    if request.method == 'POST':
        product.delete()
        return redirect('dashboard')
    return render(request, 'myapp/delete.html', {'product': product})

@login_required
def dashboard(request):
    products = Products.objects.filter(user=request.user)
    return render(request, 'myapp/dashboard.html', {'products': products})

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
    return render(request, 'myapp/register.html', {'user_form': user_form})

def invalid(request):
    return render(request, 'myapp/invalid.html')

@login_required
def my_purchases(request):
    orders = OrderDetail.objects.filter(user=request.user, has_paid=True)
    return render(request, 'myapp/purchases.html', {'orders': orders})

@login_required
def sales(request):
    orders = OrderDetail.objects.filter(product__user=request.user)
    total_sales = orders.aggregate(Sum('amount'))
    
    last_year = datetime.date.today() - datetime.timedelta(days=365)
    data = OrderDetail.objects.filter(product__user=request.user, created_on__gt=last_year)
    yearly_sales = data.aggregate(Sum('amount'))
    
    last_month = datetime.date.today() - datetime.timedelta(days=30)
    data = OrderDetail.objects.filter(product__user=request.user, created_on__gt=last_month)
    monthly_sales = data.aggregate(Sum('amount'))
    
    last_week = datetime.date.today() - datetime.timedelta(days=7)
    data = OrderDetail.objects.filter(product__user=request.user, created_on__gt=last_week)
    weekly_sales = data.aggregate(Sum('amount'))
    
    daily_sales_sums = OrderDetail.objects.filter(product__user=request.user)\
        .values('created_on__date')\
        .order_by('created_on__date')\
        .annotate(sum=Sum('amount'))
    
    product_sales_sums = OrderDetail.objects.filter(product__user=request.user)\
        .values('product__name')\
        .order_by('product__name')\
        .annotate(sum=Sum('amount'))

    return render(request, 'myapp/sales.html', {
        'total_sales': total_sales,
        'yearly_sales': yearly_sales,
        'monthly_sales': monthly_sales,
        'weekly_sales': weekly_sales,
        'daily_sales_sums': daily_sales_sums,
        'product_sales_sums': product_sales_sums
    })