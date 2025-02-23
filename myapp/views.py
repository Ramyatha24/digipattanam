from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.conf import settings
import razorpay
import json
import hmac
import hashlib
import datetime
from decimal import Decimal
from .models import Products, OrderDetail, Rating
from .forms import ProductForm, UserRegistrationForm, ContactForm
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegistrationForm, BankDetailsForm
from .models import User, BankDetails
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg
from myapp.models import Products, Rating


# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def detail(request, id):
    """
    Fetch the product with the given ID and render the detail page.
    """
    product = get_object_or_404(Products, id=id)

    # Calculate the average rating for the product
    average_rating = Rating.objects.filter(product=product).aggregate(Avg('value'))['value__avg']

    return render(request, 'myapp/detail.html', {
        'product': product,
        'average_rating': average_rating,
    })

def logout_view(request):
    """
    Handle user logout.
    """
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('login')

@login_required
def create_checkout_session(request):
    """
    Create a Razorpay checkout session for product purchase.
    """
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Products, id=product_id)

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
    """
    Verify Razorpay payment signature and update order status.
    """
    if request.method == 'POST':
        try:
            payment_response = json.loads(request.body)
            params_dict = {
                'razorpay_order_id': payment_response['razorpay_order_id'],
                'razorpay_payment_id': payment_response['razorpay_payment_id'],
                'razorpay_signature': payment_response['razorpay_signature']
            }

            client.utility.verify_payment_signature(params_dict)

            order = OrderDetail.objects.get(razorpay_order_id=params_dict['razorpay_order_id'])
            order.razorpay_payment_intent = params_dict['razorpay_payment_id']
            order.has_paid = True
            order.save()

            return JsonResponse({'status': 'success'})
        
        except (razorpay.errors.SignatureVerificationError, json.JSONDecodeError, KeyError):
            return JsonResponse({'status': 'error'})
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@csrf_exempt
def razorpay_webhook(request):
    """
    Handle Razorpay webhook events.
    """
    if request.method == "POST":
        try:
            webhook_secret = "9vGF@ge3RrLLuBu"  # Should be moved to settings.py
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
            
            if event_type in ["payment.authorized", "payment.failed", "order.paid"]:
                print(f"{event_type}:", received_data)

            return JsonResponse({"status": "Webhook received"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

def search_products(request):
    """
    Search products by name or description.
    """
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
    """
    Handle successful payment completion.
    """
    latest_order = OrderDetail.objects.filter(user=request.user, has_paid=True).last()
    return render(request, 'myapp/payment_success.html', {
        'product': latest_order.product if latest_order else None
    })

@login_required
def payment_failed(request):
    """
    Handle failed payment.
    """
    latest_order = OrderDetail.objects.filter(user=request.user, has_paid=False).last()
    return render(request, 'myapp/payment_failed.html', {
        'product': latest_order.product if latest_order else None,
        'error_message': 'Payment could not be processed'
    })

@login_required
def create_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES)
        print("Form submitted:", request.POST)  # Debug print
        if product_form.is_valid():
            print("Form is valid")  # Debug print
            new_product = product_form.save(commit=False)
            new_product.user = request.user  # Ensure user is assigned
            new_product.save()
            print("Product saved:", new_product.name)  # Debug print
            return redirect('index')  # Redirect to index after saving
        else:
            print("Form errors:", product_form.errors)  # Debug print
    
    product_form = ProductForm()
    return render(request, 'myapp/create_product.html', {'product_form': product_form})

@login_required
def submit_rating(request, product_id):
    if request.method == "POST":
        rating_value = request.POST.get("rating")
        
        if not rating_value or not (1 <= int(rating_value) <= 5):
            messages.error(request, "Invalid rating. Please submit a value between 1 and 5.")
            return redirect("purchases")

        product = get_object_or_404(Products, id=product_id)

        # Assuming there's a Rating model where users can rate products
        rating, created = Rating.objects.get_or_create(user=request.user, product=product)
        rating.value = int(rating_value)
        rating.save()

        messages.success(request, "Rating submitted successfully.")
    
    return redirect("purchases") 

def index(request):
    """
    Fetch all products and render the index page.
    """
    products = Products.objects.all()
    print("Products in index:", products)  # Debug print to check data
    return render(request, "myapp/index.html", {'products': products})

@login_required
def product_edit(request, id):
    """
    Edit an existing product.
    """
    product = get_object_or_404(Products, id=id)
    if product.user != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES, instance=product)
        if product_form.is_valid():
            product_form.save()
            return redirect('dashboard')
    else:
        product_form = ProductForm(instance=product)
    
    return render(request, 'myapp/product_edit.html', {
        'product_form': product_form,
        'product': product
    })

@login_required
def product_delete(request, id):
    """
    Delete a product.
    """
    product = get_object_or_404(Products, id=id)
    if product.user != request.user:
        return redirect('dashboard')
    
    if request.method == 'POST':
        product.delete()
        return redirect('dashboard')
    return render(request, 'myapp/delete.html', {'product': product})

@login_required
def dashboard(request):
    """
    Display user's dashboard with their products and their average ratings.
    """
    products = Products.objects.filter(user=request.user).annotate(average_rating=Avg('rating__value'))

    return render(request, 'myapp/dashboard.html', {'products': products})


def register(request):
    """
    Handle user registration.
    """
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        bank_form = BankDetailsForm(request.POST)
        
        if user_form.is_valid() and bank_form.is_valid():
            user = user_form.save()
            
            # Save bank details
            bank_details = bank_form.save(commit=False)
            bank_details.user = user
            bank_details.save()
            
            messages.success(request, 'Registration successful. Please login.')
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        bank_form = BankDetailsForm()
    
    return render(request, 'myapp/register.html', {
        'user_form': user_form,
        'bank_form': bank_form
    })

def invalid(request):
    """
    Display invalid page.
    """
    return render(request, 'myapp/invalid.html')

@login_required
def my_purchases(request):
    """
    Display user's purchase history.
    """
    orders = OrderDetail.objects.filter(user=request.user, has_paid=True)
    return render(request, 'myapp/purchases.html', {'orders': orders})

@login_required
def sales(request):
    """
    Display sales statistics and analytics.
    """
    # Base query for user's sales
    base_query = OrderDetail.objects.filter(product__user=request.user)
    
    # Calculate date ranges
    today = datetime.date.today()
    last_year = today - datetime.timedelta(days=365)
    last_month = today - datetime.timedelta(days=30)
    last_week = today - datetime.timedelta(days=7)
    
    # Calculate various sales metrics
    context = {
        'total_sales': base_query.aggregate(Sum('amount')),
        'yearly_sales': base_query.filter(created_on__gt=last_year).aggregate(Sum('amount')),
        'monthly_sales': base_query.filter(created_on__gt=last_month).aggregate(Sum('amount')),
        'weekly_sales': base_query.filter(created_on__gt=last_week).aggregate(Sum('amount')),
        'daily_sales_sums': base_query.values('created_on__date')
            .order_by('created_on__date')
            .annotate(sum=Sum('amount')),
        'product_sales_sums': base_query.values('product__name')
            .order_by('product__name')
            .annotate(sum=Sum('amount'))
    }
    
    return render(request, 'myapp/sales.html', context)

def privacy_policy(request):
    """
    Display privacy policy page.
    """
    return render(request, 'myapp/privacy.html')

def terms_of_service(request):
    """
    Display terms of service page.
    """
    return render(request, 'myapp/terms.html')

def contact(request):
    """
    Display contact form page.
    """
    form = ContactForm()
    return render(request, 'myapp/contact.html', {'form': form})

def contact_submit(request):
    """
    Handle contact form submission.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            # TODO: Implement email sending functionality
            # send_email(name, email, message)
            
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    
    return redirect('contact')

from django.http import JsonResponse
from django.conf import settings
from .models import OrderDetail, BankDetails, Products
import razorpay

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def process_payout(order_id):
    """
    Process automatic payout when an order is completed.
    """
    try:
        order = OrderDetail.objects.get(id=order_id, has_paid=True)  # Ensure order is paid
        product = order.product  # Get product
        seller = product.user  # Get seller of the product

        # Get seller's bank details
        try:
            bank_details = BankDetails.objects.get(user=seller)
        except BankDetails.DoesNotExist:
            return JsonResponse({"error": "Seller's bank details not found"}, status=400)

        # Calculate seller's payout (after 10% commission)
        commission = Decimal("0.10") * order.amount
        payout_amount = order.amount - commission

        # Create Razorpay fund transfer request
        payout_data = {
            "account_number": "3648841790",  # Replace with your Razorpay account number
            "fund_account": {
                "account_type": "bank_account",
                "bank_account": {
                    "name": bank_details.account_holder_name,
                    "ifsc": bank_details.ifsc_code,
                    "account_number": bank_details.account_number
                },
                "contact": {
                    "name": bank_details.account_holder_name,
                    "type": "vendor",
                    "email": seller.email,
                    "phone": "8374838851"  # Replace with actual seller's phone number
                }
            },
            "amount": int(payout_amount * 100),  # Razorpay requires amount in paise
            "currency": "INR",
            "mode": "IMPS",
            "purpose": "payout",
            "queue_if_low_balance": True
        }

        payout_response = client.payouts.create(payout_data)
        return JsonResponse(payout_response)

    except OrderDetail.DoesNotExist:
        return JsonResponse({"error": "Order not found or not paid"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
