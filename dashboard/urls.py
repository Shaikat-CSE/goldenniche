from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Authentication
    path('login/', views.dashboard_login, name='login'),
    path('logout/', views.dashboard_logout, name='logout'),
    
    # Dashboard home
    path('', views.dashboard_home, name='home'),
    
    # Products management
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Categories management
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Subcategories management
    path('subcategories/', views.subcategory_list, name='subcategory_list'),
    path('subcategories/create/', views.subcategory_create, name='subcategory_create'),
    path('subcategories/<int:pk>/edit/', views.subcategory_edit, name='subcategory_edit'),
    path('subcategories/<int:pk>/delete/', views.subcategory_delete, name='subcategory_delete'),
    
    # Blog categories management
    path('blog-categories/', views.blog_category_list, name='blog_category_list'),
    path('blog-categories/create/', views.blog_category_create, name='blog_category_create'),
    path('blog-categories/<int:pk>/edit/', views.blog_category_edit, name='blog_category_edit'),
    path('blog-categories/<int:pk>/delete/', views.blog_category_delete, name='blog_category_delete'),
    
    # Blogs management
    path('blogs/', views.blog_list, name='blog_list'),
    path('blogs/create/', views.blog_create, name='blog_create'),
    path('blogs/<int:pk>/edit/', views.blog_edit, name='blog_edit'),
    path('blogs/<int:pk>/delete/', views.blog_delete, name='blog_delete'),
    
    # Testimonials management
    path('testimonials/', views.testimonial_list, name='testimonial_list'),
    path('testimonials/create/', views.testimonial_create, name='testimonial_create'),
    path('testimonials/<int:pk>/edit/', views.testimonial_edit, name='testimonial_edit'),
    path('testimonials/<int:pk>/delete/', views.testimonial_delete, name='testimonial_delete'),
    path('testimonials/<int:pk>/approve/', views.testimonial_approve, name='testimonial_approve'),
    path('testimonials/<int:pk>/reject/', views.testimonial_reject, name='testimonial_reject'),
    
    # Return requests management
    path('return-requests/', views.return_request_list, name='return_request_list'),
    path('return-requests/<int:pk>/edit/', views.return_request_edit, name='return_request_edit'),
    
    # User management
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/detail/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/activity/', views.user_activity, name='user_activity'),
    path('users/<int:pk>/orders/', views.user_orders, name='user_orders'),
    path('users/<int:pk>/activate/', views.user_activate, name='user_activate'),
    path('users/<int:pk>/deactivate/', views.user_deactivate, name='user_deactivate'),
    
    # Orders management
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/invoice/', views.order_invoice, name='order_invoice'),
    path('orders/<int:pk>/status/', views.order_status_update, name='order_status'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('orders/bulk-action/', views.order_bulk_action, name='order_bulk_action'),
    
    # Activity logs
    path('activities/', views.activity_list, name='activity_list'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/mark-read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # API endpoints
    path('api/subcategories-by-category/<int:category_id>/', views.get_subcategories_by_category, name='subcategories_by_category'),
    
    # Settings
    path('settings/', views.settings, name='settings'),
] 