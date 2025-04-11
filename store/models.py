from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=200, blank=True, null=True, help_text="Title tag for SEO purposes")
    meta_description = models.TextField(blank=True, null=True, help_text="Description for search engines")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('name',)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='subcategory_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=200, blank=True, null=True, help_text="Title tag for SEO purposes")
    meta_description = models.TextField(blank=True, null=True, help_text="Description for search engines")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'SubCategories'
        ordering = ('name',)
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    def get_absolute_url(self):
        return reverse('subcategory_detail', args=[self.slug])
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField()
    short_description = models.TextField(max_length=200, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='products')
    current_stock = models.IntegerField(default=0, help_text='Current inventory stock level')
    low_stock_threshold = models.IntegerField(default=10, help_text='Send notification when stock reaches this level')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])
    
    def get_discount_percentage(self):
        if self.discount_price:
            discount = ((self.price - self.discount_price) / self.price) * 100
            return int(discount)
        return 0
    
    @property
    def is_available(self):
        return self.is_active and self.current_stock > 0
    
    @property
    def check_if_new(self):
        # Consider a product new if it was created within the last 30 days
        return (timezone.now() - self.created_at).days <= 30
    
    @property
    def check_if_on_sale(self):
        return self.discount_price is not None and self.discount_price < self.price
    
    # Add these properties to maintain compatibility with templates
    @property
    def is_new(self):
        return self.check_if_new
    
    @property
    def is_sale(self):
        return self.check_if_on_sale
    
    @property
    def stock(self):
        # For backward compatibility with templates using stock instead of current_stock
        return self.current_stock
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    def get_review_count(self):
        return self.reviews.count()

    def get_rating_distribution(self):
        distribution = self.reviews.values('rating').annotate(count=Count('id')).order_by('-rating')
        total_reviews = self.get_review_count()
        
        result = []
        for i in range(5, 0, -1):
            rating_data = next((item for item in distribution if item['rating'] == i), {'count': 0})
            percentage = (rating_data['count'] / total_reviews * 100) if total_reviews > 0 else 0
            result.append({
                'stars': i,
                'count': rating_data['count'],
                'percentage': round(percentage)
            })
        
        return result

    # Add these methods to the Product model
    average_rating = property(get_average_rating)
    review_count = property(get_review_count)
    rating_distribution = property(get_rating_distribution)

class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    RETURN_TYPE_CHOICES = [
        ('refund', 'Refund'),
        ('exchange', 'Exchange'),
    ]
    
    order_number = models.CharField(max_length=50)
    item_name = models.CharField(max_length=100)
    reason = models.TextField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    image = models.ImageField(upload_to='return_images/', blank=True, null=True)
    return_type = models.CharField(max_length=10, choices=RETURN_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Return #{self.id} - Order #{self.order_number}"
    
    class Meta:
        ordering = ['-created_at']

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date_added']
    
    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    
    def sub_total(self):
        if self.product.discount_price:
            return self.product.discount_price * self.quantity
        return self.product.price * self.quantity
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

class Wishlist(models.Model):
    wishlist_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date_added']
    
    def __str__(self):
        return self.wishlist_id

class WishlistItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.product.name

class BlogCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Blog Categories"

class Blog(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    content = models.TextField()
    created_by = models.CharField(max_length=100, default='Admin')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog_detail', args=[self.slug])
    
    def get_date(self):
        return self.created_at.strftime('%B %d, %Y')

class Testimonial(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    content = models.TextField()
    rating = models.IntegerField(default=5, choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['display_order', '-created_at']

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.is_verified}"

class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'User Addresses'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.address_line1}, {self.city}, {self.state} - {self.postal_code}"
    
    def save(self, *args, **kwargs):
        # If this address is being set as default, unset any other default addresses
        if self.is_default:
            UserAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        # If this is the user's first address, make it default
        elif not UserAddress.objects.filter(user=self.user).exists():
            self.is_default = True
        super().save(*args, **kwargs)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = "Newsletter Subscriber"
        verbose_name_plural = "Newsletter Subscribers"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Review by {self.user.username} for {self.product.name}'

class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('bkash', 'bKash'),
        ('card', 'Credit/Debit Card'),
    ]
    
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash_on_delivery')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=60.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes about this order (not visible to customers)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            last_order = Order.objects.order_by('-id').first()
            if last_order:
                last_number = int(last_order.order_number.split('#')[1])
                self.order_number = f"GN#{str(last_number + 1).zfill(6)}"
            else:
                self.order_number = "GN#000001"
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def sub_total(self):
        return self.price * self.quantity
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
