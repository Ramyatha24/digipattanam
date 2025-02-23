from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import submit_rating, process_payout

urlpatterns = [
    # Existing URLs
    path('', views.index, name='index'),
    path('product/<int:id>/', views.detail, name='detail'),
    path('create_checkout_session/', views.create_checkout_session, name='create_checkout_session'),
    path('verify/', views.verify_payment, name='verify'),
    path('search/', views.search_products, name='search_products'), 
    path('payment_success/', views.payment_success, name='payment_success'),
    path('payment_failed/', views.payment_failed, name='payment_failed'),
    path('razorpay_webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    path('createproduct/', views.create_product, name='createproduct'),
    path('editproduct/<int:id>/', views.product_edit, name='editproduct'),
    path('delete/<int:id>/', views.product_delete, name='delete'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='myapp/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('invalid/', views.invalid, name='invalid'),
    path('purchases/', views.my_purchases, name='purchases'),
    path('sales/', views.sales, name='sales'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_of_service, name='terms'),
    path('contact/', views.contact, name='contact'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('submit-rating/<int:product_id>/', submit_rating, name='submit_rating'),
    path("payout/<int:order_id>/", process_payout, name="process_payout"),
]