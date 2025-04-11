from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import ReturnRequest, Category, SubCategory, Product, Cart, CartItem, Blog, BlogCategory, Testimonial, EmailVerification, UserAddress, UserProfile, NewsletterSubscriber, Review
from django import forms

class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_number', 'item_name', 'email', 'return_type', 'status', 'created_at')
    list_filter = ('status', 'return_type', 'created_at')
    search_fields = ('order_number', 'email', 'phone', 'item_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Request Information', {
            'fields': ('order_number', 'item_name', 'reason', 'return_type', 'status')
        }),
        ('Customer Information', {
            'fields': ('email', 'phone')
        }),
        ('Additional Information', {
            'fields': ('image', 'admin_notes', 'created_at', 'updated_at')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of return requests
        return False

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'

class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category')

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        subcategory = cleaned_data.get('subcategory')
        
        # Subcategory is now optional, so we only validate if one is provided
        if category and subcategory:
            if subcategory.category != category:
                self.add_error('subcategory', 'This subcategory does not belong to the selected category')
        
        return cleaned_data

class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'price', 'current_stock', 'is_active', 'category', 'subcategory', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at', 'category', 'subcategory')
    list_editable = ('price', 'current_stock', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'subcategory')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "subcategory":
            # First, check for a POST request (save)
            if request.method == "POST" and "category" in request.POST:
                category_id = request.POST.get("category")
                if category_id:
                    kwargs["queryset"] = SubCategory.objects.filter(
                        category_id=category_id,
                        is_active=True
                    )
                else:
                    kwargs["queryset"] = SubCategory.objects.none()
            
            # Then check for a GET request with category param (loading form with category selected)
            elif request.method == "GET" and "category" in request.GET:
                category_id = request.GET.get("category")
                if category_id:
                    kwargs["queryset"] = SubCategory.objects.filter(
                        category_id=category_id,
                        is_active=True
                    )
                else:
                    kwargs["queryset"] = SubCategory.objects.none()
                    
            # For editing an existing object
            elif hasattr(request, "obj") and request.obj and request.obj.category:
                kwargs["queryset"] = SubCategory.objects.filter(
                    category=request.obj.category,
                    is_active=True
                )
            # Default case: Show all subcategories
            else:
                kwargs["queryset"] = SubCategory.objects.filter(is_active=True)
                
            # Always set required to False
            kwargs["required"] = False
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_form(self, request, obj=None, **kwargs):
        # Store the current object for later use
        request.obj = obj
        return super().get_form(request, obj, **kwargs)
    
    def save_model(self, request, obj, form, change):
        # Handle subcategory validation manually
        if obj.subcategory and obj.category:
            # Check if subcategory belongs to the category
            if obj.subcategory.category_id != obj.category.id:
                obj.subcategory = None
        
        super().save_model(request, obj, form, change)
        
    class Media:
        js = ('js/product_admin.js',)

class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'date_added')
    readonly_fields = ('date_added',)

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantity', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('quantity', 'is_active')

admin.site.register(ReturnRequest, ReturnRequestAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at', 'is_active')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'

admin.site.register(BlogCategory)

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'rating', 'is_active', 'created_at')
    list_filter = ('rating', 'is_active')
    search_fields = ('name', 'content')
    list_editable = ('is_active',)

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'code', 'created_at')

@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address_line1', 'city', 'state', 'postal_code', 'is_default')
    list_filter = ('is_default', 'created_at', 'city', 'state')
    search_fields = ('user__username', 'user__email', 'address_line1', 'city', 'state', 'postal_code')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_picture_display', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    
    def profile_picture_display(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.profile_picture.url)
        return "No Image"
    profile_picture_display.short_description = 'Profile Picture'

admin.site.register(NewsletterSubscriber)
admin.site.register(Review)
