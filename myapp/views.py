from django.shortcuts import render
from .models import Products
def index(request):
    products=Products.objects.all()
    return render(request,"myapp/index.html",{'products':products})

def detail(request, id):
    product=Products.objects.get(id=id)
    return render(request,'myapp/detail.html',{'product':product})

def dashboard(request):
    products=Products.objects.all()
    return render(request,'myapp/dashboard.html',{'products':products})


