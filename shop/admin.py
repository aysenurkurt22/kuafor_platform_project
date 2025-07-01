from django.contrib import admin
from .models import Product, Order, OrderItem, Cart, CartItem, ProductCategory, Review, Wishlist, SubscriptionProduct

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'order_date', 'total_amount', 'status', 'tracking_number', 'is_completed')
    list_filter = ('status', 'is_completed', 'order_date')
    search_fields = ('customer__username', 'tracking_number')
    raw_id_fields = ('customer',)

admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(SubscriptionProduct)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Review)
admin.site.register(Wishlist)
