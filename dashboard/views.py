from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q
from django.urls import reverse
from datetime import datetime, timedelta
import calendar
import json

from .forms import (
    DashboardLoginForm, ProductForm, CategoryForm, SubCategoryForm, 
    BlogForm, BlogCategoryForm, TestimonialForm, ReturnRequestForm, UserForm
)
from store.models import (
    Product, Category, SubCategory, Blog, BlogCategory, 
    Testimonial, ReturnRequest, Order
)
from .models import Activity, Notification, DashboardSetting

def staff_required(user):
    """Check if user is staff or superuser"""
    return user.is_staff or user.is_superuser

def dashboard_login(request):
    """Handle dashboard login"""
    if request.user.is_authenticated and staff_required(request.user):
        return redirect('dashboard:home')
        
    if request.method == 'POST':
        form = DashboardLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None and staff_required(user):
                login(request, user)
                # Create activity log
                Activity.objects.create(
                    user=user,
                    action='login',
                    entity_type='dashboard',
                    description=f"User {username} logged in"
                )
                
                # Create notification for welcome
                Notification.objects.create(
                    user=user,
                    title="Welcome back!",
                    message=f"Welcome back, {user.get_full_name() or user.username}! You've successfully logged in.",
                    level='info'
                )
                
                next_url = request.POST.get('next', 'dashboard:home')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password, or you don't have permission to access the dashboard.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = DashboardLoginForm()
        
    return render(request, 'dashboard/login.html', {'form': form})

@login_required
def dashboard_logout(request):
    """Handle dashboard logout"""
    if request.user.is_authenticated:
        # Create activity log
        Activity.objects.create(
            user=request.user,
            action='logout',
            entity_type='dashboard',
            description=f"User {request.user.username} logged out"
        )
        
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('dashboard:login')

@login_required
@user_passes_test(staff_required)
def dashboard_home(request):
    """Dashboard home view with analytics and stats"""
    # Get total counts
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_users = User.objects.count()
    pending_return_requests = ReturnRequest.objects.filter(status='pending').count()
    
    # Get order stats
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(order_status='pending').count()
    processing_orders = Order.objects.filter(order_status='processing').count()
    shipped_orders = Order.objects.filter(order_status='shipped').count()
    delivered_orders = Order.objects.filter(order_status='delivered').count()
    
    # Calculate total revenue from completed orders
    total_revenue = Order.objects.filter(
        order_status='delivered', 
        payment_status='completed'
    ).aggregate(
        total=Sum('grand_total')
    )['total'] or 0
    
    # Get recent activities
    recent_activities = Activity.objects.select_related('user').order_by('-created_at')[:10]
    
    # Get recent orders
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    # Get recent return requests
    return_requests = ReturnRequest.objects.order_by('-created_at')[:5]
    
    # Prepare monthly sales data
    today = datetime.now()
    months = []
    sales_data = []
    
    for i in range(6):
        # Get the month name for the last 6 months
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        
        # Start and end dates for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        month_name = calendar.month_name[month][:3]
        months.insert(0, f"{month_name} {str(year)[2:]}")
        
        # Get total sales for the month
        monthly_sales = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            order_status__in=['delivered', 'shipped'],
            payment_status='completed'
        ).aggregate(
            total=Sum('grand_total')
        )['total'] or 0
        
        sales_data.insert(0, float(monthly_sales))
    
    # Prepare category distribution data 
    categories = Category.objects.annotate(product_count=Count('products'))[:6]
    category_labels = [category.name for category in categories]
    category_data = [category.product_count for category in categories]
    
    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_users': total_users,
        'pending_return_requests': pending_return_requests,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'total_revenue': total_revenue,
        'recent_activities': recent_activities,
        'recent_orders': recent_orders,
        'return_requests': return_requests,
        'monthly_sales_labels': months,
        'monthly_sales_data': sales_data,
        'category_labels': category_labels,
        'category_data': category_data,
    }
    
    return render(request, 'dashboard/home.html', context)

@login_required
@user_passes_test(staff_required)
def get_subcategories_by_category(request, category_id):
    """API endpoint to get subcategories for a category"""
    subcategories = SubCategory.objects.filter(
        category_id=category_id, 
        is_active=True
    ).values('id', 'name')
    
    return JsonResponse(list(subcategories), safe=False)

# Product Management Views
@login_required
@user_passes_test(staff_required)
def product_list(request):
    """List all products"""
    products = Product.objects.select_related('category', 'subcategory').all()
    
    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
        
    # Filter by name if search query provided
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    # Filter by active status if provided
    status = request.GET.get('status')
    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)
    
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
        'status': status,
    }
    
    return render(request, 'dashboard/products/product_list.html', context)

@login_required
@user_passes_test(staff_required)
def product_create(request):
    """Create a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            
            # Auto-generate slug if not provided
            if not product.slug:
                product.slug = slugify(product.name)
                
            product.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='create',
                entity_type='product',
                entity_id=str(product.id),
                description=f"Created product: {product.name}"
            )
            
            messages.success(request, f"Product '{product.name}' created successfully")
            return redirect('dashboard:product_list')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'title': 'Create Product',
        'action': 'Create',
    }
    
    return render(request, 'dashboard/products/product_form.html', context)

@login_required
@user_passes_test(staff_required)
def product_edit(request, pk):
    """Edit an existing product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='update',
                entity_type='product',
                entity_id=str(product.id),
                description=f"Updated product: {product.name}"
            )
            
            messages.success(request, f"Product '{product.name}' updated successfully")
            return redirect('dashboard:product_list')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'title': 'Edit Product',
        'action': 'Update',
    }
    
    return render(request, 'dashboard/products/product_form.html', context)

@login_required
@user_passes_test(staff_required)
def product_delete(request, pk):
    """Delete a product"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        
        # Create activity log
        Activity.objects.create(
            user=request.user,
            action='delete',
            entity_type='product',
            entity_id=str(pk),
            description=f"Deleted product: {product_name}"
        )
        
        messages.success(request, f"Product '{product_name}' deleted successfully")
        return redirect('dashboard:product_list')
    
    context = {
        'product': product,
    }
    
    return render(request, 'dashboard/products/product_confirm_delete.html', context)

# Category Management Views
@login_required
@user_passes_test(staff_required)
def category_list(request):
    """List all categories"""
    categories = Category.objects.all()
    
    # Filter by active status if provided
    status = request.GET.get('status')
    if status == 'active':
        categories = categories.filter(is_active=True)
    elif status == 'inactive':
        categories = categories.filter(is_active=False)
    
    # Filter by name if search query provided
    search_query = request.GET.get('q')
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    
    context = {
        'categories': categories,
        'search_query': search_query,
        'status': status,
    }
    
    return render(request, 'dashboard/categories/category_list.html', context)

@login_required
@user_passes_test(staff_required)
def category_create(request):
    """Create a new category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save(commit=False)
            
            # Auto-generate slug if not provided
            if not category.slug:
                category.slug = slugify(category.name)
                
            category.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='create',
                entity_type='category',
                entity_id=str(category.id),
                description=f"Created category: {category.name}"
            )
            
            messages.success(request, f"Category '{category.name}' created successfully")
            return redirect('dashboard:category_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'title': 'Create Category',
        'action': 'Create',
    }
    
    return render(request, 'dashboard/categories/category_form.html', context)

@login_required
@user_passes_test(staff_required)
def category_edit(request, pk):
    """Edit an existing category"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='update',
                entity_type='category',
                entity_id=str(category.id),
                description=f"Updated category: {category.name}"
            )
            
            messages.success(request, f"Category '{category.name}' updated successfully")
            return redirect('dashboard:category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': 'Edit Category',
        'action': 'Update',
    }
    
    return render(request, 'dashboard/categories/category_form.html', context)

@login_required
@user_passes_test(staff_required)
def category_delete(request, pk):
    """Delete a category"""
    category = get_object_or_404(Category, pk=pk)
    
    # Check if category has products
    product_count = Product.objects.filter(category=category).count()
    
    if request.method == 'POST':
        if product_count > 0:
            messages.error(request, f"Cannot delete category '{category.name}' as it has {product_count} products associated with it.")
            return redirect('dashboard:category_list')
        
        category_name = category.name
        category.delete()
        
        # Create activity log
        Activity.objects.create(
            user=request.user,
            action='delete',
            entity_type='category',
            entity_id=str(pk),
            description=f"Deleted category: {category_name}"
        )
        
        messages.success(request, f"Category '{category_name}' deleted successfully")
        return redirect('dashboard:category_list')
    
    context = {
        'category': category,
        'product_count': product_count,
    }
    
    return render(request, 'dashboard/categories/category_confirm_delete.html', context)

# Subcategory Management Views
@login_required
@user_passes_test(staff_required)
def subcategory_list(request):
    """List all subcategories"""
    subcategories = SubCategory.objects.select_related('category').all()
    
    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        subcategories = subcategories.filter(category_id=category_id)
        
    # Filter by name if search query provided
    search_query = request.GET.get('q')
    if search_query:
        subcategories = subcategories.filter(name__icontains=search_query)
    
    # Filter by active status if provided
    status = request.GET.get('status')
    if status == 'active':
        subcategories = subcategories.filter(is_active=True)
    elif status == 'inactive':
        subcategories = subcategories.filter(is_active=False)
    
    categories = Category.objects.all()
    
    context = {
        'subcategories': subcategories,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
        'status': status,
    }
    
    return render(request, 'dashboard/subcategories/subcategory_list.html', context)

@login_required
@user_passes_test(staff_required)
def subcategory_create(request):
    """Create a new subcategory"""
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            subcategory = form.save(commit=False)
            
            # Auto-generate slug if not provided
            if not subcategory.slug:
                subcategory.slug = slugify(subcategory.name)
                
            subcategory.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='create',
                entity_type='subcategory',
                entity_id=str(subcategory.id),
                description=f"Created subcategory: {subcategory.name}"
            )
            
            messages.success(request, f"Subcategory '{subcategory.name}' created successfully")
            return redirect('dashboard:subcategory_list')
    else:
        form = SubCategoryForm()
    
    context = {
        'form': form,
        'title': 'Create Subcategory',
        'action': 'Create',
    }
    
    return render(request, 'dashboard/subcategories/subcategory_form.html', context)

@login_required
@user_passes_test(staff_required)
def subcategory_edit(request, pk):
    """Edit an existing subcategory"""
    subcategory = get_object_or_404(SubCategory, pk=pk)
    
    if request.method == 'POST':
        form = SubCategoryForm(request.POST, request.FILES, instance=subcategory)
        if form.is_valid():
            form.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='update',
                entity_type='subcategory',
                entity_id=str(subcategory.id),
                description=f"Updated subcategory: {subcategory.name}"
            )
            
            messages.success(request, f"Subcategory '{subcategory.name}' updated successfully")
            return redirect('dashboard:subcategory_list')
    else:
        form = SubCategoryForm(instance=subcategory)
    
    context = {
        'form': form,
        'subcategory': subcategory,
        'title': 'Edit Subcategory',
        'action': 'Update',
    }
    
    return render(request, 'dashboard/subcategories/subcategory_form.html', context)

@login_required
@user_passes_test(staff_required)
def subcategory_delete(request, pk):
    """Delete a subcategory"""
    subcategory = get_object_or_404(SubCategory, pk=pk)
    
    # Check if subcategory has products
    product_count = Product.objects.filter(subcategory=subcategory).count()
    
    if request.method == 'POST':
        if product_count > 0:
            messages.error(request, f"Cannot delete subcategory '{subcategory.name}' as it has {product_count} products associated with it.")
            return redirect('dashboard:subcategory_list')
        
        subcategory_name = subcategory.name
        subcategory.delete()
        
        # Create activity log
        Activity.objects.create(
            user=request.user,
            action='delete',
            entity_type='subcategory',
            entity_id=str(pk),
            description=f"Deleted subcategory: {subcategory_name}"
        )
        
        messages.success(request, f"Subcategory '{subcategory_name}' deleted successfully")
        return redirect('dashboard:subcategory_list')
    
    context = {
        'subcategory': subcategory,
        'product_count': product_count,
    }
    
    return render(request, 'dashboard/subcategories/subcategory_confirm_delete.html', context)

# User Management Views
@login_required
@user_passes_test(staff_required)
def user_list(request):
    """List all users"""
    users = User.objects.all()
    
    # Filter by active status if provided
    status = request.GET.get('status')
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    elif status == 'staff':
        users = users.filter(is_staff=True)
    elif status == 'superuser':
        users = users.filter(is_superuser=True)
    
    # Filter by username or email if search query provided
    search_query = request.GET.get('q')
    if search_query:
        users = users.filter(username__icontains=search_query) | users.filter(email__icontains=search_query)
    
    context = {
        'users': users,
        'search_query': search_query,
        'status': status,
    }
    
    return render(request, 'dashboard/users/user_list.html', context)

@login_required
@user_passes_test(staff_required)
def user_create(request):
    """Create a new user"""
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='create',
                entity_type='user',
                entity_id=str(user.id),
                description=f"Created user: {user.username}"
            )
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                title="User Created",
                message=f"User '{user.username}' was created successfully.",
                level='success'
            )
            
            messages.success(request, f"User '{user.username}' created successfully")
            return redirect('dashboard:user_list')
    else:
        form = UserForm()
    
    context = {
        'form': form,
        'title': 'Create User',
        'action': 'Create',
    }
    
    return render(request, 'dashboard/users/user_form.html', context)

@login_required
@user_passes_test(staff_required)
def user_edit(request, pk):
    """Edit an existing user"""
    user = get_object_or_404(User, pk=pk)
    
    # Prevent editing the current user
    if user == request.user:
        messages.error(request, "You cannot edit your own account from this page.")
        return redirect('dashboard:user_list')
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='update',
                entity_type='user',
                entity_id=str(user.id),
                description=f"Updated user: {user.username}"
            )
            
            messages.success(request, f"User '{user.username}' updated successfully")
            return redirect('dashboard:user_list')
    else:
        form = UserForm(instance=user)
        # Don't show password field for security
        form.fields['password'].widget.attrs['placeholder'] = 'Leave empty to keep current password'
    
    context = {
        'form': form,
        'user_obj': user,  # Use user_obj to avoid conflict with request.user
        'title': 'Edit User',
        'action': 'Update',
    }
    
    return render(request, 'dashboard/users/user_form.html', context)

@login_required
@user_passes_test(staff_required)
def user_delete(request, pk):
    """Delete a user"""
    user = get_object_or_404(User, pk=pk)
    
    # Prevent deleting the current user
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('dashboard:user_list')
    
    # Prevent deleting superuser accounts
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "You don't have permission to delete superuser accounts.")
        return redirect('dashboard:user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        
        # Create activity log
        Activity.objects.create(
            user=request.user,
            action='delete',
            entity_type='user',
            entity_id=str(pk),
            description=f"Deleted user: {username}"
        )
        
        messages.success(request, f"User '{username}' deleted successfully")
        return redirect('dashboard:user_list')
    
    context = {
        'user_obj': user,  # Use user_obj to avoid conflict with request.user
    }
    
    return render(request, 'dashboard/users/user_confirm_delete.html', context)

# Activity and Notification Views
@login_required
@user_passes_test(staff_required)
def activity_list(request):
    """List all activity logs"""
    activities = Activity.objects.select_related('user').all()
    
    # Filter by user if provided
    user_id = request.GET.get('user')
    if user_id:
        activities = activities.filter(user_id=user_id)
    
    # Filter by action if provided
    action = request.GET.get('action')
    if action:
        activities = activities.filter(action=action)
    
    # Filter by entity type if provided
    entity_type = request.GET.get('entity_type')
    if entity_type:
        activities = activities.filter(entity_type=entity_type)
    
    # Filter by description if search query provided
    search_query = request.GET.get('q')
    if search_query:
        activities = activities.filter(description__icontains=search_query)
    
    # Get unique users, actions, and entity types for filter options
    unique_users = User.objects.filter(id__in=activities.values_list('user_id', flat=True).distinct())
    unique_actions = activities.values_list('action', flat=True).distinct()
    unique_entity_types = activities.values_list('entity_type', flat=True).distinct()
    
    context = {
        'activities': activities,
        'users': unique_users,
        'actions': unique_actions,
        'entity_types': unique_entity_types,
        'selected_user': user_id,
        'selected_action': action,
        'selected_entity_type': entity_type,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/activities/activity_list.html', context)

@login_required
@user_passes_test(staff_required)
def notification_list(request):
    """List all notifications for current user"""
    # Get personal notifications
    personal_notifications = Notification.objects.filter(user=request.user)
    
    # Get global notifications
    global_notifications = Notification.objects.filter(is_global=True)
    
    # Combine both sets (avoiding duplicates)
    notifications = (personal_notifications | global_notifications).distinct().order_by('-created_at')
    
    # Filter by read status if provided
    status = request.GET.get('status')
    if status == 'read':
        notifications = notifications.filter(is_read=True)
    elif status == 'unread':
        notifications = notifications.filter(is_read=False)
    
    # Filter by notification level if provided
    level = request.GET.get('level')
    if level:
        notifications = notifications.filter(level=level)
    
    # Filter by title or message if search query provided
    search_query = request.GET.get('q')
    if search_query:
        notifications = notifications.filter(title__icontains=search_query) | notifications.filter(message__icontains=search_query)
    
    context = {
        'notifications': notifications,
        'search_query': search_query,
        'status': status,
        'level': level,
    }
    
    return render(request, 'dashboard/notifications/notification_list.html', context)

@login_required
@user_passes_test(staff_required)
def mark_notification_read(request, pk):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, pk=pk)
    
    # Only mark as read if it belongs to current user or is global
    if notification.user == request.user or notification.is_global:
        notification.is_read = True
        notification.save()
        
        messages.success(request, f"Notification '{notification.title}' marked as read")
    else:
        messages.error(request, "You don't have permission to mark this notification as read.")
    
    # Redirect back to previous page if available, otherwise to notification list
    next_url = request.GET.get('next', reverse('dashboard:notification_list'))
    return redirect(next_url)

@login_required
@user_passes_test(staff_required)
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    # Mark all personal notifications as read
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    # Mark all global notifications as read
    Notification.objects.filter(is_global=True, is_read=False).update(is_read=True)
    
    messages.success(request, "All notifications marked as read")
    
    # Redirect back to previous page if available, otherwise to notification list
    next_url = request.GET.get('next', reverse('dashboard:notification_list'))
    return redirect(next_url)

# Dashboard Settings
@login_required
@user_passes_test(staff_required)
def settings(request):
    """Dashboard settings page"""
    settings = DashboardSetting.objects.all()
    
    if request.method == 'POST':
        # Update settings
        for key, value in request.POST.items():
            # Skip CSRF token
            if key == 'csrfmiddlewaretoken':
                continue
                
            # Update or create setting
            DashboardSetting.objects.update_or_create(
                key=key,
                defaults={'value': value}
            )
            
        # Create activity log
        Activity.objects.create(
            user=request.user,
            action='update',
            entity_type='settings',
            description="Updated dashboard settings"
        )
        
        messages.success(request, "Settings updated successfully")
        return redirect('dashboard:settings')
    
    # Get settings grouped by type
    general_settings = settings.filter(key__startswith='general_')
    notification_settings = settings.filter(key__startswith='notification_')
    appearance_settings = settings.filter(key__startswith='appearance_')
    
    context = {
        'general_settings': general_settings,
        'notification_settings': notification_settings,
        'appearance_settings': appearance_settings,
    }
    
    return render(request, 'dashboard/settings/settings.html', context)

# Blog Management Views
@login_required
@user_passes_test(staff_required)
def blog_category_list(request):
    """List all blog categories"""
    categories = BlogCategory.objects.all()
    
    # Filter by name if search query provided
    search_query = request.GET.get('q')
    if search_query:
        categories = categories.filter(name__icontains=search_query)
    
    context = {
        'categories': categories,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/blogs/blog_category_list.html', context)

@login_required
@user_passes_test(staff_required)
def blog_category_create(request):
    """Create a new blog category"""
    if request.method == 'POST':
        form = BlogCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            
            # Auto-generate slug if not provided
            if not category.slug:
                category.slug = slugify(category.name)
                
            category.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='create',
                entity_type='blog_category',
                entity_id=str(category.id),
                description=f"Created blog category: {category.name}"
            )
            
            messages.success(request, f"Blog category '{category.name}' created successfully")
            return redirect('dashboard:blog_category_list')
    else:
        form = BlogCategoryForm()
    
    context = {
        'form': form,
        'title': 'Create Blog Category',
        'action': 'Create',
    }
    
    return render(request, 'dashboard/blogs/blog_category_form.html', context)

@login_required
@user_passes_test(staff_required)
def blog_category_edit(request, pk):
    """Edit an existing blog category"""
    category = get_object_or_404(BlogCategory, pk=pk)
    
    if request.method == 'POST':
        form = BlogCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='update',
                entity_type='blog_category',
                entity_id=str(category.id),
                description=f"Updated blog category: {category.name}"
            )
            
            messages.success(request, f"Blog category '{category.name}' updated successfully")
            return redirect('dashboard:blog_category_list')
    else:
        form = BlogCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': 'Edit Blog Category',
        'action': 'Update',
    }
    
    return render(request, 'dashboard/blogs/blog_category_form.html', context)

@login_required
@user_passes_test(staff_required)
def blog_category_delete(request, pk):
    """Delete a blog category"""
    category = get_object_or_404(BlogCategory, pk=pk)
    
    # Check if category has blogs
    blog_count = Blog.objects.filter(category=category).count()
    
    if request.method == 'POST':
        if blog_count > 0:
            messages.error(request, f"Cannot delete blog category '{category.name}' as it has {blog_count} blogs associated with it.")
            return redirect('dashboard:blog_category_list')
        
        category_name = category.name
        category.delete()
        
        # Create activity log
        Activity.objects.create(
            user=request.user,
            action='delete',
            entity_type='blog_category',
            entity_id=str(pk),
            description=f"Deleted blog category: {category_name}"
        )
        
        messages.success(request, f"Blog category '{category_name}' deleted successfully")
        return redirect('dashboard:blog_category_list')
    
    context = {
        'category': category,
        'blog_count': blog_count,
    }
    
    return render(request, 'dashboard/blogs/blog_category_confirm_delete.html', context)

@login_required
@user_passes_test(staff_required)
def blog_list(request):
    """List all blogs"""
    blogs = Blog.objects.select_related('category').all()
    
    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        blogs = blogs.filter(category_id=category_id)
        
    # Filter by title if search query provided
    search_query = request.GET.get('q')
    if search_query:
        blogs = blogs.filter(title__icontains=search_query)
    
    # Filter by active status if provided
    status = request.GET.get('status')
    if status == 'active':
        blogs = blogs.filter(is_active=True)
    elif status == 'inactive':
        blogs = blogs.filter(is_active=False)
    elif status == 'featured':
        blogs = blogs.filter(is_featured=True)
    
    categories = BlogCategory.objects.all()
    
    context = {
        'blogs': blogs,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
        'status': status,
    }
    
    return render(request, 'dashboard/blogs/blog_list.html', context)

@login_required
@user_passes_test(staff_required)
def blog_create(request):
    """Create a new blog post"""
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)
            
            # Auto-generate slug if not provided
            if not blog.slug:
                blog.slug = slugify(blog.title)
                
            # Set created_by to current user if not provided
            if not blog.created_by:
                blog.created_by = request.user.get_full_name() or request.user.username
                
            blog.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='create',
                entity_type='blog',
                entity_id=str(blog.id),
                description=f"Created blog post: {blog.title}"
            )
            
            messages.success(request, f"Blog post '{blog.title}' created successfully")
            return redirect('dashboard:blog_list')
    else:
        form = BlogForm()
    
    context = {
        'form': form,
        'title': 'Create Blog Post',
        'action': 'Create',
    }
    
    return render(request, 'dashboard/blogs/blog_form.html', context)

@login_required
@user_passes_test(staff_required)
def blog_edit(request, pk):
    """Edit an existing blog post"""
    blog = get_object_or_404(Blog, pk=pk)
    
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='update',
                entity_type='blog',
                entity_id=str(blog.id),
                description=f"Updated blog post: {blog.title}"
            )
            
            messages.success(request, f"Blog post '{blog.title}' updated successfully")
            return redirect('dashboard:blog_list')
    else:
        form = BlogForm(instance=blog)
    
    context = {
        'form': form,
        'blog': blog,
        'title': 'Edit Blog Post',
        'action': 'Update',
    }
    
    return render(request, 'dashboard/blogs/blog_form.html', context)

@login_required
@user_passes_test(staff_required)
def blog_delete(request, pk):
    """Delete a blog post"""
    blog = get_object_or_404(Blog, pk=pk)
    
    if request.method == 'POST':
        blog_title = blog.title
        blog.delete()
        
        # Create activity log
        Activity.objects.create(
            user=request.user,
            action='delete',
            entity_type='blog',
            entity_id=str(pk),
            description=f"Deleted blog post: {blog_title}"
        )
        
        messages.success(request, f"Blog post '{blog_title}' deleted successfully")
        return redirect('dashboard:blog_list')
    
    context = {
        'blog': blog,
    }
    
    return render(request, 'dashboard/blogs/blog_confirm_delete.html', context)

# Testimonial Management Views
@login_required
@user_passes_test(staff_required)
def testimonial_list(request):
    """List all testimonials"""
    testimonials = Testimonial.objects.all()
    
    # Filter by name if search query provided
    search_query = request.GET.get('search')
    if search_query:
        testimonials = testimonials.filter(name__icontains=search_query)
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status in ['approved', 'pending', 'rejected']:
        testimonials = testimonials.filter(status=status)
    
    # Filter by rating if provided
    rating = request.GET.get('rating')
    if rating:
        testimonials = testimonials.filter(rating=rating)
    
    context = {
        'testimonials': testimonials,
        'search_query': search_query,
        'status': status,
        'rating': rating,
    }
    
    return render(request, 'dashboard/testimonials/testimonial_list.html', context)

@login_required
@user_passes_test(staff_required)
def testimonial_create(request):
    """Create a new testimonial"""
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES)
        if form.is_valid():
            testimonial = form.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='create',
                entity_type='testimonial',
                entity_id=str(testimonial.id),
                description=f"Created testimonial from: {testimonial.name}"
            )
            
            messages.success(request, f"Testimonial from '{testimonial.name}' created successfully")
            return redirect('dashboard:testimonial_list')
    else:
        form = TestimonialForm()
    
    context = {
        'form': form,
        'title': 'Create Testimonial',
        'action': 'Create',
    }
    
    return render(request, 'dashboard/testimonials/testimonial_form.html', context)

@login_required
@user_passes_test(staff_required)
def testimonial_edit(request, pk):
    """Edit an existing testimonial"""
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    if request.method == 'POST':
        form = TestimonialForm(request.POST, request.FILES, instance=testimonial)
        if form.is_valid():
            form.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='update',
                entity_type='testimonial',
                entity_id=str(testimonial.id),
                description=f"Updated testimonial from: {testimonial.name}"
            )
            
            messages.success(request, f"Testimonial from '{testimonial.name}' updated successfully")
            return redirect('dashboard:testimonial_list')
    else:
        form = TestimonialForm(instance=testimonial)
    
    context = {
        'form': form,
        'testimonial': testimonial,
        'title': 'Edit Testimonial',
        'action': 'Update',
    }
    
    return render(request, 'dashboard/testimonials/testimonial_form.html', context)

@login_required
@user_passes_test(staff_required)
def testimonial_delete(request, pk):
    """Delete a testimonial"""
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    if request.method == 'POST':
        testimonial_name = testimonial.name
        testimonial.delete()
        
        # Create activity log
        Activity.objects.create(
            user=request.user,
            action='delete',
            entity_type='testimonial',
            entity_id=pk,
            description=f"Deleted testimonial from {testimonial_name}"
        )
        
        messages.success(request, f"Testimonial from {testimonial_name} has been deleted successfully.")
        return redirect('dashboard:testimonial_list')
    
    return render(request, 'dashboard/testimonials/testimonial_confirm_delete.html', {'testimonial': testimonial})

@login_required
@user_passes_test(staff_required)
def testimonial_approve(request, pk):
    """Approve a testimonial"""
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    testimonial.status = 'approved'
    testimonial.save()
    
    # Create activity log
    Activity.objects.create(
        user=request.user,
        action='approve',
        entity_type='testimonial',
        entity_id=pk,
        description=f"Approved testimonial from {testimonial.name}"
    )
    
    messages.success(request, f"Testimonial from {testimonial.name} has been approved.")
    return redirect('dashboard:testimonial_list')

@login_required
@user_passes_test(staff_required)
def testimonial_reject(request, pk):
    """Reject a testimonial"""
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    testimonial.status = 'rejected'
    testimonial.save()
    
    # Create activity log
    Activity.objects.create(
        user=request.user,
        action='reject',
        entity_type='testimonial',
        entity_id=pk,
        description=f"Rejected testimonial from {testimonial.name}"
    )
    
    messages.success(request, f"Testimonial from {testimonial.name} has been rejected.")
    return redirect('dashboard:testimonial_list')

@login_required
@user_passes_test(staff_required)
def user_detail(request, pk):
    """View user details"""
    user = get_object_or_404(User, pk=pk)
    
    # Get recent activities
    activities = Activity.objects.filter(user=user).order_by('-created_at')[:10]
    
    # Get recent orders
    orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get order statistics
    order_count = Order.objects.filter(user=user).count()
    completed_orders = Order.objects.filter(
        user=user, 
        order_status='delivered'
    ).count()
    
    total_spent = Order.objects.filter(
        user=user,
        order_status='delivered',
        payment_status='completed'
    ).aggregate(
        total=Sum('grand_total')
    )['total'] or 0
    
    context = {
        'user': user,
        'activities': activities,
        'orders': orders,
        'order_count': order_count,
        'completed_orders': completed_orders,
        'total_spent': total_spent,
    }
    
    return render(request, 'dashboard/users/user_detail.html', context)

@login_required
@user_passes_test(staff_required)
def user_activity(request, pk):
    """View all user activities"""
    user = get_object_or_404(User, pk=pk)
    
    # Get all activities with pagination
    activities = Activity.objects.filter(user=user).order_by('-created_at')
    
    # Filter by activity type if provided
    action_type = request.GET.get('action')
    if action_type:
        activities = activities.filter(action=action_type)
    
    # Filter by entity type if provided
    entity_type = request.GET.get('entity_type')
    if entity_type:
        activities = activities.filter(entity_type=entity_type)
    
    # Filter by search query if provided
    search_query = request.GET.get('search')
    if search_query:
        activities = activities.filter(description__icontains=search_query)
    
    context = {
        'user': user,
        'activities': activities,
        'action_type': action_type,
        'entity_type': entity_type,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/users/user_activity.html', context)

@login_required
@user_passes_test(staff_required)
def user_orders(request, pk):
    """View orders for a specific user"""
    user = get_object_or_404(User, pk=pk)
    orders = Order.objects.filter(user=user).order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        orders = orders.filter(order_status=status)
    
    # Calculate order statistics
    completed_orders = Order.objects.filter(
        user=user, 
        order_status='delivered'
    ).count()
    
    pending_user_orders = Order.objects.filter(
        user=user, 
        order_status__in=['pending', 'processing']
    ).count()
    
    total_spent = Order.objects.filter(
        user=user,
        order_status='delivered',
        payment_status='completed'
    ).aggregate(
        total=Sum('grand_total')
    )['total'] or 0
    
    context = {
        'user': user,
        'orders': orders,
        'completed_orders': completed_orders,
        'pending_user_orders': pending_user_orders,
        'total_spent': total_spent,
        'status': status,
    }
    
    return render(request, 'dashboard/users/user_orders.html', context)

@login_required
@user_passes_test(staff_required)
def user_activate(request, pk):
    """Activate a user account"""
    user = get_object_or_404(User, pk=pk)
    
    user.is_active = True
    user.save()
    
    # Create activity log
    Activity.objects.create(
        user=request.user,
        action='activate',
        entity_type='user',
        entity_id=pk,
        description=f"Activated user account for {user.username}"
    )
    
    messages.success(request, f"User account for {user.username} has been activated.")
    return redirect('dashboard:user_detail', pk=pk)

@login_required
@user_passes_test(staff_required)
def user_deactivate(request, pk):
    """Deactivate a user account"""
    user = get_object_or_404(User, pk=pk)
    
    # Prevent deactivating superuser account if current user is not a superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "You don't have permission to deactivate an admin account.")
        return redirect('dashboard:user_detail', pk=pk)
    
    user.is_active = False
    user.save()
    
    # Create activity log
    Activity.objects.create(
        user=request.user,
        action='deactivate',
        entity_type='user',
        entity_id=pk,
        description=f"Deactivated user account for {user.username}"
    )
    
    messages.success(request, f"User account for {user.username} has been deactivated.")
    return redirect('dashboard:user_detail', pk=pk)

@login_required
@user_passes_test(staff_required)
def order_list(request):
    """List all orders"""
    orders = Order.objects.all().order_by('-created_at')
    
    # Get counts for each order status
    pending_count = Order.objects.filter(order_status='pending').count()
    processing_count = Order.objects.filter(order_status='processing').count()
    shipped_count = Order.objects.filter(order_status='shipped').count()
    delivered_count = Order.objects.filter(order_status='delivered').count()
    cancelled_count = Order.objects.filter(order_status='cancelled').count()
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        orders = orders.filter(order_status=status)
    
    # Filter by search query if provided
    search_query = request.GET.get('search')
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    context = {
        'orders': orders,
        'status': status,
        'search_query': search_query,
        'pending_count': pending_count,
        'processing_count': processing_count, 
        'shipped_count': shipped_count,
        'delivered_count': delivered_count,
        'cancelled_count': cancelled_count,
        'total_count': orders.count(),
    }
    
    return render(request, 'dashboard/orders/order_list.html', context)

@login_required
@user_passes_test(staff_required)
def order_detail(request, pk):
    """View order details"""
    order = get_object_or_404(Order, pk=pk)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'dashboard/orders/order_detail.html', context)

@login_required
@user_passes_test(staff_required)
def order_invoice(request, pk):
    """View order invoice"""
    order = get_object_or_404(Order, pk=pk)
    order_items = order.items.all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'dashboard/orders/order_invoice.html', context)

@login_required
@user_passes_test(staff_required)
def order_status_update(request, pk):
    """Update order status"""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        # Handle admin notes update
        if 'admin_notes' in request.POST:
            order.admin_notes = request.POST.get('admin_notes')
            order.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='update',
                entity_type='order',
                entity_id=str(order.id),
                description=f"Updated admin notes for order #{order.order_number}"
            )
            
            messages.success(request, "Admin notes updated successfully.")
            return redirect('dashboard:order_detail', pk=pk)
    
    # Handle status updates via GET
    status_type = request.GET.get('status_type', '')
    status = request.GET.get('status', '')
    
    if status_type and status:
        old_status = None
        
        if status_type == 'payment':
            old_status = order.payment_status
            order.payment_status = status
            message = f"Updated payment status to {order.get_payment_status_display()}"
        elif status_type == 'order':
            old_status = order.order_status
            order.order_status = status
            message = f"Updated order status to {order.get_order_status_display()}"
        else:
            messages.error(request, "Invalid status type provided.")
            return redirect('dashboard:order_detail', pk=pk)
        
        order.save()
        
        # Create activity log
        Activity.objects.create(
            user=request.user,
            action='update',
            entity_type='order',
            entity_id=str(order.id),
            description=message
        )
        
        # Create notification for customer if they have a user account
        if order.user:
            Notification.objects.create(
                user=order.user,
                title=f"Order #{order.order_number} Update",
                message=message,
                level='info'
            )
        
        messages.success(request, message)
    else:
        messages.error(request, "Missing status parameters.")
    
    return redirect('dashboard:order_detail', pk=pk)

@login_required
@user_passes_test(staff_required)
def return_request_list(request):
    """List all return requests"""
    return_requests = ReturnRequest.objects.all().order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        return_requests = return_requests.filter(status=status)
    
    # Filter by search query
    search_query = request.GET.get('q')
    if search_query:
        return_requests = return_requests.filter(
            order_number__icontains=search_query
        )
    
    context = {
        'return_requests': return_requests,
        'selected_status': status,
        'search_query': search_query,
    }
    
    return render(request, 'dashboard/returns/return_request_list.html', context)

@login_required
@user_passes_test(staff_required)
def return_request_edit(request, pk):
    """Edit a return request status"""
    return_request = get_object_or_404(ReturnRequest, pk=pk)
    
    if request.method == 'POST':
        form = ReturnRequestForm(request.POST, instance=return_request)
        if form.is_valid():
            old_status = return_request.status
            updated_request = form.save()
            
            # Create activity log
            Activity.objects.create(
                user=request.user,
                action='update',
                entity_type='return_request',
                entity_id=str(return_request.id),
                description=f"Updated return request #{return_request.id} status from {old_status} to {updated_request.status}"
            )
            
            messages.success(request, f"Return request #{return_request.id} updated successfully")
            return redirect('dashboard:return_request_list')
    else:
        form = ReturnRequestForm(instance=return_request)
    
    context = {
        'form': form,
        'return_request': return_request,
        'title': f'Edit Return Request #{return_request.id}',
        'action': 'Update',
    }
    
    return render(request, 'dashboard/returns/return_request_form.html', context)

@login_required
@user_passes_test(staff_required)
def order_delete(request, pk):
    """Delete an order"""
    order = get_object_or_404(Order, pk=pk)
    order_number = order.order_number
    
    # Create activity log before deletion
    Activity.objects.create(
        user=request.user,
        action='delete',
        entity_type='order',
        entity_id=str(pk),
        description=f"Deleted order #{order_number}"
    )
    
    # Delete the order
    order.delete()
    
    messages.success(request, f"Order #{order_number} has been deleted successfully.")
    return redirect('dashboard:order_list')

@login_required
@user_passes_test(staff_required)
def order_bulk_action(request):
    """Process bulk actions for orders"""
    if request.method == 'POST':
        action = request.POST.get('action')
        order_ids = request.POST.getlist('order_ids')
        
        if not order_ids:
            messages.error(request, "No orders were selected for the action.")
            return redirect('dashboard:order_list')
        
        # Valid status actions
        valid_actions = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        
        if action not in valid_actions:
            messages.error(request, f"Invalid action: {action}")
            return redirect('dashboard:order_list')
        
        # Get the orders
        orders = Order.objects.filter(id__in=order_ids)
        count = orders.count()
        
        # Update all orders at once
        orders.update(order_status=action)
        
        # Log activities for each order
        for order in orders:
            Activity.objects.create(
                user=request.user,
                action='update',
                entity_type='order',
                entity_id=str(order.id),
                description=f"Changed order #{order.order_number} status to {action} (bulk action)"
            )
            
            # Create notification for customer if they have a user account
            if order.user:
                Notification.objects.create(
                    user=order.user,
                    title=f"Order #{order.order_number} Update",
                    message=f"Your order status has been updated to: {action}",
                    level='info'
                )
        
        action_display = action.replace('_', ' ').title()
        messages.success(request, f"Successfully updated {count} orders to '{action_display}' status.")
    
    return redirect('dashboard:order_list') 