from django.urls import path
from . import views

urlpatterns = [
    # Home and static pages
    path('', views.index, name='home'),
    path('retiqospices/', views.retiqo_spices, name='retiqo_spices'),
    path('premiumfruits/', views.premium_fruits, name='premium_fruits'),
    path('prestigecookware/', views.prestige_cookware, name='prestige_cookware'),
    path('homedecor/', views.home_decor, name='home_decor'),
    path('hot-deals/', views.hot_deals, name='hot_deals'),
    path('bakeryingredients/', views.bakery_ingredients, name='bakeryingredients'),
    path('blog/', views.blog, name='blog'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('blog/category/<slug:slug>/', views.blog_category, name='blog_category'),
    path('my-account/', views.my_account, name='my_account'),
    path('about-us/', views.about_us, name='about_us'),
    path('checkout/', views.checkout, name='checkout'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('orders-returns/', views.orders_returns, name='orders_returns'),
    
    # Product URLs
    path('products/', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='products_by_category'),
    path('product/<slug:product_slug>/', views.product_detail, name='product_detail'),
    
    # Cart URLs
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('remove-cart-item/<int:product_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('get-cart-count/', views.get_cart_count, name='get_cart_count'),
    path('get-cart-items/', views.get_cart_items, name='get_cart_items'),
    
    # Wishlist URLs
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('get-wishlist-count/', views.get_wishlist_count, name='get_wishlist_count'),
    
    # Order URLs
    path('place-order/', views.place_order, name='place_order'),
    path('order-complete/<str:order_number>/', views.order_complete, name='order_complete'),
    path('order-tracking/<str:order_number>/', views.order_tracking, name='order_tracking'),
    
    # Return URLs
    path('return-request/', views.orders_returns, name='return_request'),
    path('return-policy/', views.return_policy, name='return_policy'),
    
    # Search and Filter URLs
    path('search/', views.search, name='search'),
    path('filter/', views.filter_products, name='filter_products'),
    path('filter/<slug:category_slug>/', views.filter_products, name='filter_products_by_category'),
    path('ajax-filter/', views.ajax_filter_products, name='ajax_filter_products'),
    
    # Admin helper URLs
    path('get-subcategories/', views.get_subcategories, name='get_subcategories'),
    path('admin/store/get-subcategories/', views.get_subcategories, name='admin_get_subcategories'),
    
    # Test URLs for subcategory data
    path('test-subcategories/', views.test_subcategories, name='test_subcategories'),
    
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/<str:token>/', views.resend_verification, name='resend_verification'),

    # User Account URLs
    path('my-account/update-profile/', views.update_profile, name='update_profile'),
    path('my-account/change-password/', views.change_password, name='change_password'),
    path('my-account/add-address/', views.add_address, name='add_address'),
    path('my-account/edit-address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('my-account/delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('my-account/set-default-address/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('my-account/get-wishlist-items/', views.get_wishlist_items_json, name='get_wishlist_items_json'),
    path('my-account/get-orders/', views.get_orders_json, name='get_orders_json'),
    
    # Test 404 page
    path('test-404/', views.test_404, name='test_404'),
    
    # Test 500 page
    path('test-500/', views.test_500, name='test_500'),

    # Newsletter Signup URL
    path('newsletter-signup/', views.newsletter_signup, name='newsletter_signup'),
    
    # Product Review URL
    path('product/<int:product_id>/add-review/', views.add_review, name='add_review'),
] 