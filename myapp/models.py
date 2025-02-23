from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import razorpay
from django.conf import settings

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class Products(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('video', 'Video File'),
        ('audio', 'Audio File'),
        ('image', 'Image File'),
        ('zip', 'ZIP Archive'),
        ('doc', 'Document'),
        ('other', 'Other')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200)
    desc = models.CharField(max_length=1000)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    file = models.FileField(upload_to='uploads')
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        default='other',
        help_text="Select the type of file you are uploading",
        null=True
    )

    def __str__(self):
        return self.name
    
    @property
    def total_sales(self):
        return OrderDetail.objects.filter(product=self, has_paid=True).count()
    
    @property
    def total_sales_amount(self):
        orders = OrderDetail.objects.filter(product=self, has_paid=True)
        return sum(order.amount for order in orders)

class OrderDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    customer_email = models.EmailField(null=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_payment_intent = models.CharField(max_length=200, null=True)
    razorpay_order_id = models.CharField(max_length=100, unique=True, null=True)
    has_paid = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"Order by {self.user.username} for {self.product.name}"

from django.contrib.auth.models import User

class BankDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bank_details', null=True)
    bank_name = models.CharField(max_length=100, null=True)
    account_holder_name = models.CharField(max_length=100, null=True)
    account_number = models.CharField(max_length=20, null=True)
    ifsc_code = models.CharField(max_length=11, null=True)
    branch_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.account_holder_name} - {self.bank_name}"
    
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE, null=True)
    value = models.IntegerField(default=1, null=True)

    class Meta:
        unique_together = ('user', 'product')