from django.contrib import admin

from .models import Products, OrderDetail

admin.site.register(Products)
admin.site.register(OrderDetail)

