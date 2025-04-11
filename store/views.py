from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Q, Sum, Min, Max
from .forms import ReturnRequestForm, UserRegistrationForm, EmailVerificationForm, UserLoginForm, UserProfileUpdateForm, AddressForm, ReviewForm
from .models import ReturnRequest, Category, Product, Cart, CartItem, Wishlist, WishlistItem, Blog, BlogCategory, Testimonial, SubCategory, EmailVerification, UserAddress, UserProfile, NewsletterSubscriber, Review, Order, OrderItem
from decimal import Decimal
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.db import models
import logging
from django.views.decorators.csrf import csrf_exempt
import json
import math
import random
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm

logger = logging.getLogger(__name__)

# Helper function to get cart ID from session
def _cart_id(request):
    cart_id = request.session.session_key
    if not cart_id:
        request.session.save()
        cart_id = request.session.session_key
    return cart_id

# Helper function to get wishlist ID from session
def _wishlist_id(request):
    wishlist_id = request.session.session_key
    if not wishlist_id:
        request.session.save()
        wishlist_id = request.session.session_key
    return wishlist_id

def index(request):
    # Get featured products across all categories
    products = Product.objects.filter(is_active=True).order_by('-created_at')[:30]
    
    # Get hot deals (products with discount)
    hot_deals = Product.objects.filter(
        is_active=True, 
        discount_price__isnull=False
    ).filter(discount_price__lt=models.F('price')).order_by('-created_at')[:6]
    
    # Get new arrivals - use created_at date to determine newest products
    # instead of the removed is_new field
    new_arrivals = Product.objects.filter(
        is_active=True
    ).order_by('-created_at')[:6]
    
    # Get the 5 main categories
    spices_category = Category.objects.filter(name__icontains='Spice').first()
    fruits_category = Category.objects.filter(name__icontains='Fruit').first()
    cookware_category = Category.objects.filter(name__icontains='Cookware').first()
    decor_category = Category.objects.filter(name__icontains='Decor').first()
    bakery_category = Category.objects.filter(name__icontains='Bakery').first()
    
    # Make sure we have products from each category for the tabs
    category_products = []
    
    if spices_category:
        spice_products = Product.objects.filter(category=spices_category, is_active=True).order_by('-created_at')[:6]
        category_products.extend(spice_products)
        
    if fruits_category:
        fruit_products = Product.objects.filter(category=fruits_category, is_active=True).order_by('-created_at')[:6]
        category_products.extend(fruit_products)
        
    if cookware_category:
        cookware_products = Product.objects.filter(category=cookware_category, is_active=True).order_by('-created_at')[:6]
        category_products.extend(cookware_products)
        
    if decor_category:
        decor_products = Product.objects.filter(category=decor_category, is_active=True).order_by('-created_at')[:6]
        category_products.extend(decor_products)
        
    if bakery_category:
        bakery_products = Product.objects.filter(category=bakery_category, is_active=True).order_by('-created_at')[:6]
        category_products.extend(bakery_products)
    
    # If we don't have enough products from the individual category queries, add them to our main products list
    if category_products:
        # Convert to list to combine with featured products
        all_products = list(products)
        
        # Add category products not already in the list
        for product in category_products:
            if product not in all_products:
                all_products.append(product)
        
        # Use combined list
        products = all_products
    
    categories = Category.objects.filter(is_active=True)
    testimonials = Testimonial.objects.filter(is_active=True)
    
    # Get wishlist items
    wishlist_product_ids = []
    try:
        wishlist = Wishlist.objects.get(wishlist_id=_wishlist_id(request))
        wishlist_items = WishlistItem.objects.filter(wishlist=wishlist)
        wishlist_product_ids = [item.product.id for item in wishlist_items]
    except Wishlist.DoesNotExist:
        pass
    
    return render(request, 'store/index.html', {
        'products': products,
        'hot_deals': hot_deals,
        'new_arrivals': new_arrivals,
        'categories': categories,
        'wishlist_product_ids': wishlist_product_ids,
        'testimonials': testimonials,
    })

def retiqo_spices(request):
    # Get spices category
    category = Category.objects.filter(name__icontains='Spices').first()
    
    if not category:
        # If category doesn't exist, return empty products and subcategories
        products = Product.objects.none()
        subcategories = SubCategory.objects.none()
        selected_subcategory = None
        selected_subcategories = []
        min_price = None
        max_price = None
        sort_by = None
        show = None
        top_selling_products = []
    else:
        # Get all subcategories for this category
        subcategories = SubCategory.objects.filter(category=category, is_active=True)
        
        # Initialize products queryset
        products = Product.objects.filter(category=category, is_active=True)
        
        # Get top selling products for this category
        top_selling_products = Product.objects.filter(
            category=category,
            is_active=True,
            is_featured=True  # Products marked as featured are considered top selling
        ).order_by('-created_at')[:5]  # Get the 5 most recent featured products
        
        # Filter by subcategory if specified (single subcategory - legacy support)
        subcategory_id = request.GET.get('subcategory')
        selected_subcategory = None
        if subcategory_id:
            try:
                selected_subcategory = int(subcategory_id)
                products = products.filter(subcategory_id=selected_subcategory)
            except (ValueError, TypeError):
                pass
        
        # Filter by multiple subcategories using subcategory_id parameter
        subcategory_ids = request.GET.getlist('subcategory_id')
        selected_subcategories = []
        if subcategory_ids:
            try:
                # Convert to integers and filter
                selected_subcategories = [int(id) for id in subcategory_ids if id.isdigit()]
                if selected_subcategories:
                    products = products.filter(subcategory_id__in=selected_subcategories)
            except (ValueError, TypeError):
                pass
        
        # Filter by price range
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price and max_price:
            try:
                min_price = float(min_price)
                max_price = float(max_price)
                products = products.filter(price__gte=min_price, price__lte=max_price)
            except (ValueError, TypeError):
                pass
        
        # Apply sorting
        sort_by = request.GET.get('sort_by')
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'popular':
            products = products.order_by('-is_featured', '-created_at')
        
        # Get products per page
        show = request.GET.get('show')
        per_page = 12  # Default
        if show and show == '1':
            per_page = 24
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, per_page if 'per_page' in locals() else 12)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    # Build pagination parameters string for template
    pagination_params = ''
    
    # Add min_price and max_price if present
    if min_price:
        pagination_params += f'&min_price={min_price}'
    if max_price:
        pagination_params += f'&max_price={max_price}'
    
    # Add sort_by if present
    if sort_by:
        pagination_params += f'&sort_by={sort_by}'
    
    # Add show parameter if present
    if show:
        pagination_params += f'&show={show}'
    
    # Add subcategory_id parameters
    if selected_subcategories:
        for subcategory_id in selected_subcategories:
            pagination_params += f'&subcategory_id={subcategory_id}'
    
    # Pass products and subcategories to the template
    context = {
        'products': products,
        'product_count': products.paginator.count if hasattr(products, 'paginator') else 0,
        'category': category,
        'subcategories': subcategories,
        'selected_subcategory': selected_subcategory,
        'selected_subcategories': selected_subcategories,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'show': show,
        'pagination_params': pagination_params,
        'top_selling_products': top_selling_products
    }
    return render(request, 'store/retiqospices.html', context)

def premium_fruits(request):
    # Get premium fruits category
    category = Category.objects.filter(name__icontains='Premium Fruits').first()
    
    if not category:
        # If category doesn't exist, return empty products and subcategories
        products = Product.objects.none()
        subcategories = SubCategory.objects.none()
        selected_subcategory = None
        selected_subcategories = []
        min_price = None
        max_price = None
        sort_by = None
        show = None
        top_selling_products = []  # Add empty list for top selling products
    else:
        # Get all subcategories for this category
        subcategories = SubCategory.objects.filter(category=category, is_active=True)
        
        # Initialize products queryset
        products = Product.objects.filter(category=category, is_active=True)
        
        # Get top selling products for this category
        top_selling_products = Product.objects.filter(
            category=category,
            is_active=True,
            is_featured=True  # Products marked as featured are considered top selling
        ).order_by('-created_at')[:5]  # Get the 5 most recent featured products
        
        # Filter by subcategory if specified (single subcategory - legacy support)
        subcategory_id = request.GET.get('subcategory')
        selected_subcategory = None
        if subcategory_id:
            try:
                selected_subcategory = int(subcategory_id)
                products = products.filter(subcategory_id=selected_subcategory)
            except (ValueError, TypeError):
                pass
        
        # Filter by multiple subcategories using subcategory_id parameter
        subcategory_ids = request.GET.getlist('subcategory_id')
        selected_subcategories = []
        if subcategory_ids:
            try:
                # Convert to integers and filter
                selected_subcategories = [int(id) for id in subcategory_ids if id.isdigit()]
                if selected_subcategories:
                    products = products.filter(subcategory_id__in=selected_subcategories)
            except (ValueError, TypeError):
                pass
        
        # Filter by price range
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price and max_price:
            try:
                min_price = float(min_price)
                max_price = float(max_price)
                products = products.filter(price__gte=min_price, price__lte=max_price)
            except (ValueError, TypeError):
                pass
        
        # Apply sorting
        sort_by = request.GET.get('sort_by')
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'popular':
            products = products.order_by('-is_featured', '-created_at')
        
        # Get products per page
        show = request.GET.get('show')
        per_page = 12  # Default
        if show and show == '1':
            per_page = 24
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, per_page if 'per_page' in locals() else 12)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    # Build pagination parameters string for template
    pagination_params = ''
    
    # Add min_price and max_price if present
    if min_price:
        pagination_params += f'&min_price={min_price}'
    if max_price:
        pagination_params += f'&max_price={max_price}'
    
    # Add sort_by if present
    if sort_by:
        pagination_params += f'&sort_by={sort_by}'
    
    # Add show parameter if present
    if show:
        pagination_params += f'&show={show}'
    
    # Add subcategory_id parameters
    if selected_subcategories:
        for subcategory_id in selected_subcategories:
            pagination_params += f'&subcategory_id={subcategory_id}'
    
    # Pass products and subcategories to the template
    context = {
        'products': products,
        'product_count': products.paginator.count if hasattr(products, 'paginator') else 0,
        'category': category,
        'subcategories': subcategories,
        'selected_subcategory': selected_subcategory,
        'selected_subcategories': selected_subcategories,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'show': show,
        'pagination_params': pagination_params,
        'top_selling_products': top_selling_products
    }
    return render(request, 'store/premiumfruits.html', context)

def prestige_cookware(request):
    # Get prestige cookware category
    category = Category.objects.filter(name__icontains='Prestige Cookware').first()
    
    if not category:
        # If category doesn't exist, return empty products and subcategories
        products = Product.objects.none()
        subcategories = SubCategory.objects.none()
        selected_subcategory = None
        selected_subcategories = []
        min_price = None
        max_price = None
        sort_by = None
        show = None
        top_selling_products = []
    else:
        # Get all subcategories for this category
        subcategories = SubCategory.objects.filter(category=category, is_active=True)
        
        # Initialize products queryset
        products = Product.objects.filter(category=category, is_active=True)
        
        # Get top selling products in this category (based on is_featured flag)
        top_selling_products = Product.objects.filter(
            category=category, 
            is_active=True, 
            is_featured=True
        ).order_by('-created_at')[:5]
        
        # Filter by subcategory if specified (single subcategory - legacy support)
        subcategory_id = request.GET.get('subcategory')
        selected_subcategory = None
        if subcategory_id:
            try:
                selected_subcategory = int(subcategory_id)
                products = products.filter(subcategory_id=selected_subcategory)
            except (ValueError, TypeError):
                pass
        
        # Filter by multiple subcategories using subcategory_id parameter
        subcategory_ids = request.GET.getlist('subcategory_id')
        selected_subcategories = []
        if subcategory_ids:
            try:
                # Convert to integers and filter
                selected_subcategories = [int(id) for id in subcategory_ids if id.isdigit()]
                if selected_subcategories:
                    products = products.filter(subcategory_id__in=selected_subcategories)
            except (ValueError, TypeError):
                pass
        
        # Filter by price range
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price and max_price:
            try:
                min_price = float(min_price)
                max_price = float(max_price)
                products = products.filter(price__gte=min_price, price__lte=max_price)
            except (ValueError, TypeError):
                pass
        
        # Apply sorting
        sort_by = request.GET.get('sort_by')
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'popular':
            products = products.order_by('-is_featured', '-created_at')
        
        # Get products per page
        show = request.GET.get('show')
        per_page = 12  # Default
        if show and show == '1':
            per_page = 24
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, per_page if 'per_page' in locals() else 12)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    # Build pagination parameters string for template
    pagination_params = ''
    
    # Add min_price and max_price if present
    if min_price:
        pagination_params += f'&min_price={min_price}'
    if max_price:
        pagination_params += f'&max_price={max_price}'
    
    # Add sort_by if present
    if sort_by:
        pagination_params += f'&sort_by={sort_by}'
    
    # Add show parameter if present
    if show:
        pagination_params += f'&show={show}'
    
    # Add subcategory_id parameters
    if selected_subcategories:
        for subcategory_id in selected_subcategories:
            pagination_params += f'&subcategory_id={subcategory_id}'
    
    # Pass products and subcategories to the template
    context = {
        'products': products,
        'product_count': products.paginator.count if hasattr(products, 'paginator') else 0,
        'category': category,
        'subcategories': subcategories,
        'selected_subcategory': selected_subcategory,
        'selected_subcategories': selected_subcategories,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'show': show,
        'pagination_params': pagination_params,
        'top_selling_products': top_selling_products
    }
    return render(request, 'store/prestigecookware.html', context)

def home_decor(request):
    # Get home decor category
    category = Category.objects.filter(name__icontains='Home Decor').first()
    
    if not category:
        # If category doesn't exist, return empty products and subcategories
        products = Product.objects.none()
        subcategories = SubCategory.objects.none()
        selected_subcategory = None
        selected_subcategories = []
        min_price = None
        max_price = None
        sort_by = None
        show = None
        top_selling_products = []
        min_db_price = 0
        max_db_price = 50000  # Default if no products exist
    else:
        # Get all subcategories for this category
        subcategories = SubCategory.objects.filter(category=category, is_active=True)
        
        # Initialize products queryset
        all_category_products = Product.objects.filter(category=category, is_active=True)
        
        # Get the min and max price of products in this category for dynamic price slider
        price_range = all_category_products.aggregate(
            min_price=models.Min('price'),
            max_price=models.Max('price')
        )
        
        min_db_price = price_range['min_price'] or 0
        max_db_price = price_range['max_price'] or 50000
        
        # Round min_db_price down to nearest hundred and max_db_price up to nearest hundred
        min_db_price = math.floor(min_db_price / 100) * 100
        max_db_price = math.ceil(max_db_price / 100) * 100
        
        # Start with all products and apply filters
        products = all_category_products
        
        # Get top selling products in this category (based on is_featured flag or sales count if available)
        top_selling_products = Product.objects.filter(
            category=category, 
            is_active=True, 
            is_featured=True
        ).order_by('-created_at')[:3]
        
        # Filter by subcategory if specified (single subcategory - legacy support)
        subcategory_id = request.GET.get('subcategory')
        selected_subcategory = None
        if subcategory_id:
            try:
                selected_subcategory = int(subcategory_id)
                products = products.filter(subcategory_id=selected_subcategory)
            except (ValueError, TypeError):
                pass
        
        # Filter by multiple subcategories using subcategory_id parameter
        subcategory_ids = request.GET.getlist('subcategory_id')
        selected_subcategories = []
        if subcategory_ids:
            try:
                # Convert to integers and filter
                selected_subcategories = [int(id) for id in subcategory_ids if id.isdigit()]
                if selected_subcategories:
                    products = products.filter(subcategory_id__in=selected_subcategories)
            except (ValueError, TypeError):
                pass
        
        # Filter by price range
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price and max_price:
            try:
                min_price = float(min_price)
                max_price = float(max_price)
                products = products.filter(price__gte=min_price, price__lte=max_price)
            except (ValueError, TypeError):
                pass
        
        # Apply sorting
        sort_by = request.GET.get('sort_by')
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'popular':
            products = products.order_by('-is_featured', '-created_at')
        
        # Get products per page
        show = request.GET.get('show')
        per_page = 12  # Default
        if show and show in ['24', '36']:
            per_page = int(show)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, per_page if 'per_page' in locals() else 12)
    
    try:
        paginated_products = paginator.page(page)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)
    
    # Build pagination parameters string for template
    pagination_params = ''
    
    # Add min_price and max_price if present
    if min_price:
        pagination_params += f'&min_price={min_price}'
    if max_price:
        pagination_params += f'&max_price={max_price}'
    
    # Add sort_by if present
    if sort_by:
        pagination_params += f'&sort_by={sort_by}'
    
    # Add show parameter if present
    if show:
        pagination_params += f'&show={show}'
    
    # Add subcategory_id parameters
    if 'selected_subcategories' in locals() and selected_subcategories:
        for subcategory_id in selected_subcategories:
            pagination_params += f'&subcategory_id={subcategory_id}'
    
    # Prepare context dictionary
    context = {
        'products': paginated_products,
        'product_count': products.count(),
        'category': category,
        'subcategories': subcategories,
        'selected_subcategory': selected_subcategory if 'selected_subcategory' in locals() else None,
        'selected_subcategories': selected_subcategories if 'selected_subcategories' in locals() else [],
        'min_price': min_price,
        'max_price': max_price,
        'min_db_price': min_db_price,
        'max_db_price': max_db_price,
        'sort_by': sort_by,
        'show': show,
        'pagination_params': pagination_params,
        'top_selling_products': top_selling_products
    }
    
    return render(request, 'store/homedecor.html', context)

def bakery_ingredients(request):
    # Get bakery ingredients category
    category = Category.objects.filter(name__icontains='Bakery').first()
    
    if not category:
        # If category doesn't exist, return empty products and subcategories
        products = Product.objects.none()
        subcategories = SubCategory.objects.none()
        selected_subcategory = None
        selected_subcategories = []
        min_price = None
        max_price = None
        sort_by = None
        show = None
        top_selling_products = []
        min_db_price = 0
        max_db_price = 10000  # Default if no products exist
    else:
        # Get all subcategories for this category
        subcategories = SubCategory.objects.filter(category=category, is_active=True)
        
        # Initialize products queryset
        all_category_products = Product.objects.filter(category=category, is_active=True)
        
        # Get the min and max price of products in this category for dynamic price slider
        price_range = all_category_products.aggregate(
            min_price=models.Min('price'),
            max_price=models.Max('price')
        )
        
        min_db_price = price_range['min_price'] or 0
        max_db_price = price_range['max_price'] or 10000
        
        # Round min_db_price down to nearest hundred and max_db_price up to nearest hundred
        min_db_price = math.floor(min_db_price / 100) * 100
        max_db_price = math.ceil(max_db_price / 100) * 100
        
        # Start with all products and apply filters
        products = all_category_products
    
        # Filter by subcategory if specified (single subcategory - legacy support)
        subcategory_id = request.GET.get('subcategory')
        selected_subcategory = None
        if subcategory_id:
            try:
                selected_subcategory = int(subcategory_id)
                products = products.filter(subcategory_id=selected_subcategory)
            except (ValueError, TypeError):
                pass
        
        # Filter by multiple subcategories using subcategory_id parameter
        subcategory_ids = request.GET.getlist('subcategory_id')
        selected_subcategories = []
        if subcategory_ids:
            try:
                # Convert to integers and filter
                selected_subcategories = [int(id) for id in subcategory_ids if id.isdigit()]
                if selected_subcategories:
                    products = products.filter(subcategory_id__in=selected_subcategories)
            except (ValueError, TypeError):
                pass
        
        # Filter by price range
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price and max_price:
            try:
                min_price = float(min_price)
                max_price = float(max_price)
                products = products.filter(price__gte=min_price, price__lte=max_price)
            except (ValueError, TypeError):
                pass
        
        # Apply sorting
        sort_by = request.GET.get('sort_by')
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'popular':
            products = products.order_by('-is_featured', '-created_at')
        
        # Get products per page
        show = request.GET.get('show')
        per_page = 12  # Default
        if show and show in ['24', '36']:
            per_page = int(show)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, per_page if 'per_page' in locals() else 12)
    
    try:
        paginated_products = paginator.page(page)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)
    
    # Build pagination parameters string for template
    pagination_params = ''
    
    # Add min_price and max_price if present
    if min_price:
        pagination_params += f'&min_price={min_price}'
    if max_price:
        pagination_params += f'&max_price={max_price}'
    
    # Add sort_by if present
    if sort_by:
        pagination_params += f'&sort_by={sort_by}'
    
    # Add show parameter if present
    if show:
        pagination_params += f'&show={show}'
    
    # Add subcategory_id parameters
    if 'selected_subcategories' in locals() and selected_subcategories:
        for subcategory_id in selected_subcategories:
            pagination_params += f'&subcategory_id={subcategory_id}'
    
    # Get top selling products
    top_selling_products = Product.objects.filter(
        category=category,
        is_active=True,
        is_featured=True
    ).order_by('-created_at')[:5] if category else []
    
    # Prepare context dictionary
    context = {
        'products': paginated_products,
        'subcategories': subcategories,
        'selected_subcategory': selected_subcategory if 'selected_subcategory' in locals() else None,
        'selected_subcategories': selected_subcategories if 'selected_subcategories' in locals() else [],
        'min_price': min_price,
        'max_price': max_price,
        'min_db_price': min_db_price,
        'max_db_price': max_db_price,
        'sort_by': sort_by,
        'show': show,
        'pagination_params': pagination_params,
        'top_selling_products': top_selling_products
    }
    
    return render(request, 'store/bakeryingredients.html', context)

def blog(request):
    # Get all blog posts
    posts = Blog.objects.all()
    
    # Get featured post
    featured_post = Blog.objects.filter(is_featured=True).first()
    
    # If no featured post is set, use the most recent post
    if not featured_post and posts.exists():
        featured_post = posts.first()
    
    # Get all categories
    categories = BlogCategory.objects.all()
    
    # Get recent posts (excluding the featured post)
    if featured_post:
        recent_posts = posts.exclude(id=featured_post.id)[:5]
    else:
        recent_posts = posts[:5]
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(posts, 6)  # Show 6 posts per page
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    context = {
        'posts': posts,
        'featured_post': featured_post,
        'categories': categories,
        'recent_posts': recent_posts,
    }
    
    return render(request, 'store/blog.html', context)

def blog_detail(request, slug):
    # Get the blog post
    post = get_object_or_404(Blog, slug=slug)
    
    # Get all categories
    categories = BlogCategory.objects.all()
    
    # Get recent posts
    recent_posts = Blog.objects.exclude(id=post.id)[:5]
    
    # Get related posts (from the same category)
    related_posts = Blog.objects.filter(category=post.category).exclude(id=post.id)[:3]
    
    context = {
        'post': post,
        'categories': categories,
        'recent_posts': recent_posts,
        'related_posts': related_posts,
    }
    
    return render(request, 'store/blog-detail.html', context)

def blog_category(request, slug):
    # Get the category
    category = get_object_or_404(BlogCategory, slug=slug)
    
    # Get posts in this category
    posts = Blog.objects.filter(category=category)
    
    # Get all categories
    categories = BlogCategory.objects.all()
    
    # Get recent posts
    recent_posts = Blog.objects.all()[:5]
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(posts, 6)  # Show 6 posts per page
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'posts': posts,
        'categories': categories,
        'recent_posts': recent_posts,
    }
    
    return render(request, 'store/blog-category.html', context)

def about_us(request):
    return render(request, 'store/about-us.html')

def hot_deals(request):
    # Get the 5 main categories
    main_categories = Category.objects.filter(
        name__in=['Retiqo Spices', 'Premium Fruits', 'Prestige Cookware', 'Home Decor', 'Bakery Ingredients']
    ).order_by('name')
    
    # Get products that are on sale (have a discount_price)
    all_deal_products = Product.objects.filter(is_active=True, discount_price__isnull=False)
    
    # Ensure the discount price is actually less than the regular price
    all_deal_products = all_deal_products.filter(discount_price__lt=models.F('price'))
    
    # Get top selling products based on is_featured flag and having a discount
    top_selling_products = Product.objects.filter(
        is_active=True, 
        is_featured=True,
        discount_price__isnull=False,
        discount_price__lt=models.F('price')
    ).order_by('-created_at')[:5]
    
    # Get min and max prices from the database for slider
    min_db_price = all_deal_products.aggregate(Min('price'))['price__min'] or 0
    max_db_price = all_deal_products.aggregate(Max('price'))['price__max'] or 10000
    
    # Round min_db_price down to nearest hundred and max_db_price up to nearest hundred
    min_db_price = math.floor(min_db_price / 100) * 100
    max_db_price = math.ceil(max_db_price / 100) * 100
    
    # Apply filters to products - start with all products
    products = all_deal_products
    
    # Filter by category if specified
    category_ids = request.GET.getlist('category_id')
    selected_categories = []
    if category_ids:
        try:
            # Convert to integers and filter
            selected_categories = [int(id) for id in category_ids if id.isdigit()]
            if selected_categories:
                products = products.filter(category_id__in=selected_categories)
        except (ValueError, TypeError):
            pass
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and max_price:
        try:
            min_price = float(min_price)
            max_price = float(max_price)
            products = products.filter(price__gte=min_price, price__lte=max_price)
        except (ValueError, TypeError):
            pass
    
    # Apply sorting
    sort_by = request.GET.get('sort_by')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        products = products.order_by('-is_featured', '-created_at')
    
    # Get total number of products before pagination
    total_products = products.count()
    
    # Get products per page
    show = request.GET.get('show')
    per_page = 12  # Default to 12 products per page
    
    # Handle show parameter
    if show:
        try:
            show_value = int(show)
            if show_value in [12, 24]:
                per_page = show_value
        except (ValueError, TypeError):
            pass
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, per_page)
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    # Build pagination parameters string for template
    pagination_params = ''
    
    # Add min_price and max_price if present
    if min_price:
        pagination_params += f'&min_price={min_price}'
    if max_price:
        pagination_params += f'&max_price={max_price}'
    
    # Add sort_by if present
    if sort_by:
        pagination_params += f'&sort_by={sort_by}'
    
    # Add show parameter if present
    if show:
        pagination_params += f'&show={show}'
    
    # Add category_id parameters
    if selected_categories:
        for category_id in selected_categories:
            pagination_params += f'&category_id={category_id}'
    
    # Pass products and categories to the template
    context = {
        'products': products,
        'main_categories': main_categories,
        'selected_categories': selected_categories,
        'min_price': min_price,
        'max_price': max_price,
        'min_db_price': min_db_price,
        'max_db_price': max_db_price,
        'sort_by': sort_by,
        'show': show,
        'pagination_params': pagination_params,
        'top_selling_products': top_selling_products,
        'total_products': total_products
    }
    return render(request, 'store/hot-deals.html', context)

@login_required
def my_account(request):
    # Get user's orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Get user's wishlist items
    try:
        wishlist = Wishlist.objects.get(wishlist_id=_wishlist_id(request))
        wishlist_items = WishlistItem.objects.filter(wishlist=wishlist)
    except (Wishlist.DoesNotExist, WishlistItem.DoesNotExist):
        wishlist_items = []
    
    # Get user's addresses
    addresses = UserAddress.objects.filter(user=request.user)
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Initialize forms
    profile_form = UserProfileUpdateForm(instance=request.user)
    address_form = AddressForm()
    password_form = PasswordChangeForm(request.user)
    
    context = {
        'user': request.user,
        'profile': profile,
        'orders': orders,
        'wishlist_items': wishlist_items,
        'addresses': addresses,
        'profile_form': profile_form,
        'address_form': address_form,
        'password_form': password_form,
    }
    
    return render(request, 'store/my-account.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('my_account')
        else:
            return render(request, 'store/my-account.html', {
                'profile_form': form,
                'active_tab': 'profile'
            })
    return redirect('my_account')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: update the session to prevent logging out
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('my_account')
        else:
            return render(request, 'store/my-account.html', {
                'password_form': form,
                'active_tab': 'profile'
            })
    return redirect('my_account')

@login_required
def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = UserAddress(
                user=request.user,
                address_line1=form.cleaned_data['address_line1'],
                address_line2=form.cleaned_data['address_line2'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                postal_code=form.cleaned_data['postal_code'],
                phone=form.cleaned_data['phone'],
                is_default=form.cleaned_data['is_default']
            )
            address.save()
            messages.success(request, 'Address added successfully.')
            return redirect('my_account')
        else:
            return render(request, 'store/my-account.html', {
                'address_form': form,
                'active_tab': 'address'
            })
    return redirect('my_account')

@login_required
def edit_address(request, address_id):
    try:
        address = UserAddress.objects.get(id=address_id, user=request.user)
        
        if request.method == 'POST':
            form = AddressForm(request.POST)
            if form.is_valid():
                address.address_line1 = form.cleaned_data['address_line1']
                address.address_line2 = form.cleaned_data['address_line2']
                address.city = form.cleaned_data['city']
                address.state = form.cleaned_data['state']
                address.postal_code = form.cleaned_data['postal_code']
                address.phone = form.cleaned_data['phone']
                address.is_default = form.cleaned_data['is_default']
                address.save()
                messages.success(request, 'Address updated successfully.')
                return redirect('my_account')
        else:
            # Populate form with existing address data
            initial_data = {
                'address_line1': address.address_line1,
                'address_line2': address.address_line2 or '',
                'city': address.city,
                'state': address.state,
                'postal_code': address.postal_code,
                'phone': address.phone,
                'is_default': address.is_default
            }
            form = AddressForm(initial=initial_data)
            
            return render(request, 'store/edit-address.html', {
                'form': form,
                'address': address
            })
            
    except UserAddress.DoesNotExist:
        messages.error(request, 'Address not found.')
        return redirect('my_account')

@login_required
def delete_address(request, address_id):
    try:
        address = UserAddress.objects.get(id=address_id, user=request.user)
        was_default = address.is_default
        address.delete()
        
        # If we deleted the default address, set another one as default
        if was_default:
            remaining_address = UserAddress.objects.filter(user=request.user).first()
            if remaining_address:
                remaining_address.is_default = True
                remaining_address.save()
                
        messages.success(request, 'Address deleted successfully.')
    except UserAddress.DoesNotExist:
        messages.error(request, 'Address not found.')
    
    return redirect('my_account')

@login_required
def set_default_address(request, address_id):
    try:
        address = UserAddress.objects.get(id=address_id, user=request.user)
        # Clear any existing default addresses
        UserAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
        # Set the new default
        address.is_default = True
        address.save()
        messages.success(request, 'Default address updated successfully.')
    except UserAddress.DoesNotExist:
        messages.error(request, 'Address not found.')
    
    return redirect('my_account')

@login_required
def get_wishlist_items_json(request):
    try:
        wishlist = Wishlist.objects.get(wishlist_id=_wishlist_id(request))
        wishlist_items = WishlistItem.objects.filter(wishlist=wishlist)
        
        items = []
        for item in wishlist_items:
            product = item.product
            items.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': float(product.discount_price if product.discount_price else product.price),
                'regular_price': float(product.price),
                'discount_percentage': product.get_discount_percentage(),
                'image_url': product.image.url if product.image else '',
                'category': product.category.name
            })
        
        return JsonResponse({
            'items': items,
            'count': len(items)
        })
    except (Wishlist.DoesNotExist, WishlistItem.DoesNotExist):
        return JsonResponse({
            'items': [],
            'count': 0
        })

@login_required
def get_orders_json(request):
    # Get user's orders from the database
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Format orders for JSON response
    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.order_number,
            'date': order.created_at.strftime('%B %d, %Y'),
            'status': order.order_status.capitalize(),
            'total': float(order.grand_total),
        })
    
    return JsonResponse({
        'orders': orders_data,
        'count': len(orders_data)
    })

def register(request):
    if request.user.is_authenticated:
        return redirect('my_account')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User will be activated after email verification
            user.save()
            
            # Generate verification token and code
            token = get_random_string(length=64)
            verification_code = ''.join(random.choices('0123456789', k=6))
            
            # Save verification details
            email_verification = EmailVerification.objects.create(
                user=user,
                token=token,
                code=verification_code
            )
            
            # Send verification email
            send_verification_email(user, token, verification_code)
            
            # Redirect to verification page
            return redirect('verify_email', token=token)
    else:
        form = UserRegistrationForm()
    
    return render(request, 'store/register.html', {'form': form})

def verify_email(request, token):
    try:
        verification = EmailVerification.objects.get(token=token)
        
        if verification.is_verified:
            messages.info(request, 'Your email is already verified. Please login.')
            return redirect('login')
            
        if request.method == 'POST':
            form = EmailVerificationForm(request.POST)
            if form.is_valid():
                entered_code = form.cleaned_data['verification_code']
                
                if entered_code == verification.code:
                    # Mark as verified and activate user
                    verification.is_verified = True
                    verification.save()
                    
                    user = verification.user
                    user.is_active = True
                    user.save()
                    
                    messages.success(request, 'Email verification successful! You can now login.')
                    return redirect('login')
                else:
                    messages.error(request, 'Invalid verification code. Please try again.')
        else:
            form = EmailVerificationForm()
            
        return render(request, 'store/verify-email.html', {'form': form, 'token': token})
        
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('register')

def resend_verification(request, token):
    try:
        verification = EmailVerification.objects.get(token=token)
        
        if verification.is_verified:
            messages.info(request, 'Your email is already verified. Please login.')
            return redirect('login')
            
        # Generate a new verification code
        new_code = ''.join(random.choices('0123456789', k=6))
        verification.code = new_code
        verification.save()
        
        # Resend verification email
        send_verification_email(verification.user, verification.token, new_code)
        
        messages.success(request, 'Verification code has been resent to your email.')
        return redirect('verify_email', token=token)
        
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('register')

def send_verification_email(user, token, code):
    subject = 'Verify your Golden Niche account'
    message = f'''
    Hello {user.first_name},
    
    Thank you for registering at Golden Niche BD. To complete your registration, please use the following verification code:
    
    {code}
    
    Alternatively, you can click on the link below:
    http://{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'}/verify/{token}/
    
    If you did not register for an account, please ignore this email.
    
    Best regards,
    Golden Niche BD Team
    '''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def login_view(request):
    if request.user.is_authenticated:
        return redirect('my_account')
        
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Check if input is an email
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                    username = user.username
                except User.DoesNotExist:
                    pass
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'my_account')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'store/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')
    
def password_reset_request(request):
    # Password reset functionality will go here
    pass

@login_required
def checkout(request):
    # Get cart using cart_id from session instead of user
    cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
    if not cart or not cart.items.exists():
        messages.error(request, 'Your cart is empty')
        return redirect('cart')
    
    # Calculate totals
    subtotal = sum(item.sub_total() for item in cart.items.all())
    shipping_cost = Decimal('60.00')  # Fixed shipping cost
    tax = subtotal * Decimal('0.15')  # 15% tax
    grand_total = subtotal + shipping_cost + tax
    
    context = {
        'cart': cart,
        'cart_items': cart.items.all() if cart else [],
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/place-order.html', context)

@login_required
def order_complete(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    return render(request, 'store/order-complete.html', {
        'order': order,
        'order_items': order_items,
    })

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'review': {
                        'user': review.user.username,
                        'rating': review.rating,
                        'comment': review.comment,
                        'created_at': review.created_at.strftime('%d %b %Y, %I:%M %p')
                    },
                    'review_count': product.reviews.count()
                })
            
            messages.success(request, 'Your review has been added successfully!')
            return redirect('product_detail', slug=product.slug)
    
    return redirect('product_detail', slug=product.slug)

def orders_returns(request):
    """
    View for displaying the orders and returns page
    """
    return render(request, 'store/orders-returns.html')

def handler404(request, exception):
    """
    Custom 404 error handler
    """
    return render(request, 'store/404.html', status=404)

def handler500(request):
    """
    Custom 500 error handler
    """
    return render(request, 'store/500.html', status=500)

def handler403(request, exception):
    """
    Custom 403 error handler
    """
    return render(request, 'store/403.html', status=403)

def handler400(request, exception):
    """
    Custom 400 error handler
    """
    return render(request, 'store/400.html', status=400)

def privacy_policy(request):
    """
    View for displaying the privacy policy page
    """
    return render(request, 'store/privacy-policy.html')

def terms_conditions(request):
    """
    View for displaying the terms and conditions page
    """
    return render(request, 'store/terms-conditions.html')

def contact_us(request):
    """
    View for displaying the contact us page
    """
    return render(request, 'store/contact-us.html')

def product_list(request, category_slug=None):
    """
    View for displaying a list of products, optionally filtered by category
    """
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category, is_active=True)
    else:
        products = Product.objects.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
        'category': category if category_slug else None,
    }
    return render(request, 'store/product-list.html', context)

def product_detail(request, product_slug):
    """
    View for displaying product details
    """
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    reviews = Review.objects.filter(product=product)
    related_products = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
    }
    return render(request, 'store/product-detail.html', context)

def cart(request):
    """
    View for displaying the cart
    """
    cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
    context = {
        'cart': cart,
        'cart_items': cart.items.all() if cart else [],
    }
    return render(request, 'store/cart.html', context)

def add_to_cart(request, product_id):
    """
    View for adding a product to the cart
    """
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))
    
    # Check if product is already in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart_count = cart.items.count()
        return JsonResponse({
            'status': 'success',
            'message': f'{product.name} added to cart',
            'cart_count': cart_count
        })
    
    messages.success(request, f'{product.name} added to cart')
    return redirect('cart')

def remove_from_cart(request, product_id):
    """
    View for removing a product from the cart
    """
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
    
    if cart:
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        if cart_item:
            cart_item.delete()
    
    messages.success(request, f'{product.name} removed from cart')
    return redirect('cart')

def remove_cart_item(request, product_id):
    """
    View for removing a cart item
    """
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
    
    if cart:
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        if cart_item:
            cart_item.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart_count = cart.items.count() if cart else 0
        return JsonResponse({
            'status': 'success',
            'message': f'{product.name} removed from cart',
            'cart_count': cart_count
        })
    
    messages.success(request, f'{product.name} removed from cart')
    return redirect('cart')

def update_cart(request):
    """
    View for updating cart quantities
    """
    if request.method == 'POST':
        cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
        if cart:
            for item in cart.items.all():
                quantity = request.POST.get(f'quantity_{item.product.id}')
                if quantity:
                    try:
                        quantity = int(quantity)
                        if quantity > 0:
                            item.quantity = quantity
                            item.save()
                        else:
                            item.delete()
                    except ValueError:
                        pass
    
    return redirect('cart')

def get_cart_count(request):
    """
    View for getting the cart count
    """
    cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
    count = cart.items.count() if cart else 0
    
    return JsonResponse({'count': count})

def get_cart_items(request):
    """
    View for getting cart items
    """
    cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
    items = []
    
    if cart:
        for item in cart.items.all():
            items.append({
                'id': item.product.id,
                'name': item.product.name,
                'slug': item.product.slug,
                'price': float(item.product.discount_price if item.product.discount_price else item.product.price),
                'quantity': item.quantity,
                'subtotal': float(item.sub_total()),
                'image_url': item.product.image.url if item.product.image else '',
            })
    
    return JsonResponse({'items': items})

def wishlist(request):
    """
    View for displaying the wishlist
    """
    wishlist = Wishlist.objects.filter(wishlist_id=_wishlist_id(request)).first()
    context = {
        'wishlist': wishlist,
        'wishlist_items': WishlistItem.objects.filter(wishlist=wishlist) if wishlist else [],
    }
    return render(request, 'store/wishlist.html', context)

def add_to_wishlist(request, product_id):
    """
    View for adding a product to the wishlist
    """
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(wishlist_id=_wishlist_id(request))
    
    # Check if product is already in wishlist
    wishlist_item, created = WishlistItem.objects.get_or_create(
        wishlist=wishlist,
        product=product
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        wishlist_count = WishlistItem.objects.filter(wishlist=wishlist).count()
        return JsonResponse({
            'status': 'success',
            'message': f'{product.name} added to wishlist',
            'wishlist_count': wishlist_count
        })
    
    messages.success(request, f'{product.name} added to wishlist')
    return redirect('wishlist')

def remove_from_wishlist(request, product_id):
    """
    View for removing a product from the wishlist
    """
    product = get_object_or_404(Product, id=product_id)
    wishlist = Wishlist.objects.filter(wishlist_id=_wishlist_id(request)).first()
    
    if wishlist:
        wishlist_item = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()
        if wishlist_item:
            wishlist_item.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        wishlist_count = WishlistItem.objects.filter(wishlist=wishlist).count() if wishlist else 0
        return JsonResponse({
            'status': 'success',
            'message': f'{product.name} removed from wishlist',
            'wishlist_count': wishlist_count
        })
    
    messages.success(request, f'{product.name} removed from wishlist')
    return redirect('wishlist')

def get_wishlist_count(request):
    """
    View for getting the wishlist count
    """
    wishlist = Wishlist.objects.filter(wishlist_id=_wishlist_id(request)).first()
    count = WishlistItem.objects.filter(wishlist=wishlist).count() if wishlist else 0
    
    return JsonResponse({'count': count})

def place_order(request):
    """
    View for placing an order
    """
    if request.method == 'POST':
        cart = Cart.objects.filter(cart_id=_cart_id(request)).first()
        if not cart or not cart.items.exists():
            messages.error(request, 'Your cart is empty')
            return redirect('cart')
        
        # Calculate totals
        subtotal = sum(item.sub_total() for item in cart.items.all())
        shipping_cost = Decimal('60.00')  # Convert to Decimal
        tax = Decimal('0.00')  # Convert to Decimal
        grand_total = subtotal + shipping_cost + tax
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            order_number=f'GN{random.randint(1000, 9999)}',
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            email=request.POST.get('email', ''),
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            country=request.POST.get('country', ''),
            zip_code=request.POST.get('zip_code', ''),
            phone=request.POST.get('phone', ''),
            payment_method=request.POST.get('payment_method', 'cash_on_delivery'),
            payment_status='pending',
            order_status='pending',
            shipping_cost=shipping_cost,
            tax=tax,
            grand_total=grand_total,
            notes=request.POST.get('notes', '')
        )
        
        # Create order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # Clear cart
        cart.delete()
        
        messages.success(request, 'Your order has been placed successfully')
        return redirect('order_complete', order_number=order.order_number)
    
    return redirect('checkout')

def order_tracking(request, order_number):
    """
    View for tracking an order
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'store/order-tracking.html', context)

def return_policy(request):
    """
    View for displaying the return policy
    """
    return render(request, 'store/return-policy.html')

def search(request):
    """
    View for searching products
    """
    query = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'store/search-results.html', context)

def filter_products(request, category_slug=None):
    """
    View for filtering products
    """
    products = Product.objects.filter(is_active=True)
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Apply filters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if min_price and max_price:
        try:
            min_price = float(min_price)
            max_price = float(max_price)
            products = products.filter(price__gte=min_price, price__lte=max_price)
        except ValueError:
            pass
    
    # Apply sorting
    sort_by = request.GET.get('sort_by')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    context = {
        'products': products,
        'category': category if category_slug else None,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    return render(request, 'store/filtered-products.html', context)

def ajax_filter_products(request):
    """
    View for AJAX filtering of products
    """
    products = Product.objects.filter(is_active=True)
    
    # Apply filters
    category_id = request.GET.get('category')
    if category_id:
        try:
            category_id = int(category_id)
            products = products.filter(category_id=category_id)
        except ValueError:
            pass
    
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if min_price and max_price:
        try:
            min_price = float(min_price)
            max_price = float(max_price)
            products = products.filter(price__gte=min_price, price__lte=max_price)
        except ValueError:
            pass
    
    # Apply sorting
    sort_by = request.GET.get('sort_by')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    
    # Prepare product data for JSON response
    product_data = []
    for product in products:
        product_data.append({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': float(product.price),
            'image_url': product.image.url if product.image else '',
            'category': product.category.name,
        })
    
    return JsonResponse({'products': product_data})

def get_subcategories(request):
    """
    View for getting subcategories for a category
    """
    category_id = request.GET.get('category_id')
    subcategories = []
    
    if category_id:
        try:
            category_id = int(category_id)
            subcategories = SubCategory.objects.filter(category_id=category_id, is_active=True)
        except ValueError:
            pass
    
    subcategory_data = [{'id': sub.id, 'name': sub.name} for sub in subcategories]
    return JsonResponse({'subcategories': subcategory_data})

def test_subcategories(request):
    """
    View for testing subcategory data
    """
    categories = Category.objects.filter(is_active=True)
    subcategories = SubCategory.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
        'subcategories': subcategories,
    }
    return render(request, 'store/test-subcategories.html', context)

def test_404(request):
    """
    View for testing 404 error page
    """
    raise Http404("This is a test 404 error")

def test_500(request):
    """
    View for testing 500 error page
    """
    raise Exception("This is a test 500 error")

def newsletter_signup(request):
    """
    View for newsletter signup
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            NewsletterSubscriber.objects.get_or_create(email=email)
            messages.success(request, 'Thank you for subscribing to our newsletter!')
        else:
            messages.error(request, 'Please provide a valid email address.')
    
    return redirect('home')