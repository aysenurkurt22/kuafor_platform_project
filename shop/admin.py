from django.contrib import admin
from .models import Product, Order, OrderItem, Cart, CartItem, ProductCategory, Review, Wishlist, SubscriptionProduct

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_date', 'total_price', 'status', 'tracking_number', 'is_completed')
    list_filter = ('status', 'is_completed', 'order_date')
    search_fields = ('user__username', 'tracking_number')
    raw_id_fields = ('user',)

admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(SubscriptionProduct)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Review)
admin.site.register(Wishlist)
