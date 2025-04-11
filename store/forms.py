from django import forms
from .models import Product, SubCategory, UserProfile, Review
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User

class ReturnRequestForm(forms.Form):
    order_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your order number'})
    )
    item_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the item name'})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Please explain why you want to return this item'}),
        required=True
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'})
    )
    image = forms.ImageField(
        required=False,
        help_text='Upload an image of the item (optional)'
    )
    
    RETURN_CHOICES = [
        ('refund', 'I want a refund'),
        ('exchange', 'I want to exchange for another item'),
    ]
    
    return_type = forms.ChoiceField(
        choices=RETURN_CHOICES,
        widget=forms.RadioSelect(),
        required=True
    )

# Add ProductAdminForm at the end of the file
class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get the initial category value if it exists
        initial_category = None
        if 'instance' in kwargs and kwargs['instance']:
            initial_category = kwargs['instance'].category
        
        # Filter subcategories based on initial category
        if initial_category:
            self.fields['subcategory'].queryset = SubCategory.objects.filter(category=initial_category)
        else:
            self.fields['subcategory'].queryset = SubCategory.objects.none()

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        max_length=254, 
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    username = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email address already exists")
        return email

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

class EmailVerificationForm(forms.Form):
    verification_code = forms.CharField(
        max_length=6,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter 6-digit verification code'})
    )

class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        max_length=254, 
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    username = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control-file'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Try to get profile picture from user's profile if it exists
        if self.instance:
            try:
                self.fields['profile_picture'].initial = self.instance.profile.profile_picture
            except (AttributeError, UserProfile.DoesNotExist):
                pass
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email exists and is not the current user's email
        if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Email address already exists")
        return email
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check if username exists and is not the current user's username
        if User.objects.filter(username=username).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Username already exists")
        return username
        
    def save(self, commit=True):
        user = super().save(commit=True)
        profile_picture = self.cleaned_data.get('profile_picture')
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Update profile picture if provided
        if profile_picture:
            profile.profile_picture = profile_picture
            profile.save()
            
        return user

class AddressForm(forms.Form):
    address_line1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'})
    )
    address_line2 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2 (Optional)'})
    )
    city = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'})
    )
    state = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Division'})
    )
    postal_code = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'})
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    is_default = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'input-rating'}),
            'comment': forms.Textarea(attrs={'class': 'input', 'placeholder': 'Your Review'}),
        } 