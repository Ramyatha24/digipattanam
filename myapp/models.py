from django.db import models
from django.contrib.auth.models import User

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
    price = models.FloatField()
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
    user=models.ForeignKey(User,on_delete=models.CASCADE, null=True)
    customer_email = models.EmailField(null=True)  # Email address of the customer
    product = models.ForeignKey(Products, on_delete=models.CASCADE)  # Link to the purchased product
    amount = models.IntegerField()  # Total amount of the order in paise (or your chosen currency unit)
    razorpay_payment_intent = models.CharField(max_length=200, null=True)  # Razorpay payment ID for reference
    razorpay_order_id=models.CharField(max_length=100,unique=True, null=True)
    has_paid = models.BooleanField(default=False)  # Flag to check payment status
    created_on = models.DateTimeField(auto_now_add=True, null=True)  # Timestamp when the order was created
    updated_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"Order by{self.user.username} for {self.product.name}"
