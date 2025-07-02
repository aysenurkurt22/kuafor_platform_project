from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('add_to_cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('update_cart_item/<int:pk>/', views.update_cart_item, name='update_cart_item'),
    path('remove_from_cart/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('order_success/', views.order_success, name='order_success'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('wishlist/', views.wishlist_detail, name='wishlist_detail'),
    path('add_to_wishlist/<int:pk>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove_from_wishlist/<int:pk>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('subscription_products/', views.subscription_product_list, name='subscription_product_list'),
    path('subscription_product/<int:pk>/', views.subscription_product_detail, name='subscription_product_detail'),
    path('add_subscription_to_cart/<int:pk>/', views.add_subscription_to_cart, name='add_subscription_to_cart'),
    path('iyzico_callback/', views.iyzico_callback, name='iyzico_callback'), # Iyzico callback URL'si eklendi
]