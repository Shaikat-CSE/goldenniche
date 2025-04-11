from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from store.models import Product, Category, SubCategory, Blog, BlogCategory, Testimonial, ReturnRequest

class DashboardLoginForm(AuthenticationForm):
    """Custom login form for dashboard"""
    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Username'}
    ))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Password'}
    ))
    
    class Meta:
        model = User
        fields = ['username', 'password']

class UserForm(forms.ModelForm):
    """Form for user management"""
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Password'}
    ), required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class ProductForm(forms.ModelForm):
    """Form for product management"""
    class Meta:
        model = Product
        fields = ['category', 'subcategory', 'name', 'slug', 'description', 
                  'short_description', 'price', 'discount_price', 'image', 
                  'current_stock', 'low_stock_threshold', 'is_active', 'is_featured']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'subcategory': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CategoryForm(forms.ModelForm):
    """Form for category management"""
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'image', 'is_active', 'meta_title', 'meta_description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SubCategoryForm(forms.ModelForm):
    """Form for subcategory management"""
    class Meta:
        model = SubCategory
        fields = ['category', 'name', 'slug', 'description', 'image', 'is_active', 'meta_title', 'meta_description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BlogCategoryForm(forms.ModelForm):
    """Form for blog category management"""
    class Meta:
        model = BlogCategory
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }

class BlogForm(forms.ModelForm):
    """Form for blog management"""
    class Meta:
        model = Blog
        fields = ['title', 'slug', 'category', 'image', 'short_description', 
                 'content', 'created_by', 'is_active', 'is_featured']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'created_by': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TestimonialForm(forms.ModelForm):
    """Form for testimonial management"""
    class Meta:
        model = Testimonial
        fields = ['name', 'company', 'position', 'image', 'content', 'rating', 'is_active', 'is_featured', 'display_order', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class ReturnRequestForm(forms.ModelForm):
    """Form for return request management"""
    class Meta:
        model = ReturnRequest
        fields = ['order_number', 'item_name', 'reason', 'email', 'phone', 
                 'image', 'return_type', 'status', 'admin_notes']
        widgets = {
            'order_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'readonly': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'return_type': forms.Select(attrs={'class': 'form-select', 'readonly': True}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        } 