from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Products, BankDetails

class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = ['name', 'desc', 'price', 'file', 'image', 'file_type']
        widgets = {
            'file_type': forms.Select(attrs={'class': 'form-control'}),
        }

class BankDetailsForm(forms.Form):
    bank_name = forms.CharField(label='Bank Name', max_length=100)
    account_holder_name = forms.CharField(label='Account Holder Name', max_length=100)
    account_number = forms.CharField(label='Account Number', max_length=20)
    ifsc_code = forms.CharField(label='IFSC Code', max_length=11)
    branch_name = forms.CharField(label='Branch Name', max_length=100, required=False)

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name']
        
    def clean_password2(self):
        cd = self.cleaned_data
        if 'password' in cd and 'password2' in cd:
            if cd['password'] != cd['password2']:
                raise forms.ValidationError('Password fields do not match')
            return cd['password2']
        raise forms.ValidationError('Both password fields are required')
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control bg-gray-700 text-white border-none focus:ring focus:ring-green-200 focus:ring-opacity-50 rounded-md',
        'placeholder': 'Your Name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control bg-gray-700 text-white border-none focus:ring focus:ring-green-200 focus:ring-opacity-50 rounded-md',
        'placeholder': 'Your Email'
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control bg-gray-700 text-white border-none focus:ring focus:ring-green-200 focus:ring-opacity-50 rounded-md',
        'placeholder': 'Your Message',
        'rows': 5
    }))

class BankDetailsForm(forms.ModelForm):
    class Meta:
        model = BankDetails
        fields = ['bank_name', 'account_holder_name', 'account_number', 'ifsc_code', 'branch_name']