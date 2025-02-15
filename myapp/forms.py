from django import forms
from .models import Products
from django.contrib.auth.models import User

class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = ['name', 'desc', 'price', 'file', 'image', 'file_type']
        widgets = {
            'file_type': forms.Select(attrs={'class': 'form-control'}),
        }

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