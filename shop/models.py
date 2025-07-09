import uuid
from django.db import models
from django.conf import settings

class ProductCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(ProductCategory, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_orders', null=True, blank=True)
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    order_date = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    subscription_product = models.ForeignKey('SubscriptionProduct', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.price * self.quantity

    def __str__(self):
        product_name = self.product.name if self.product else (self.subscription_product.name if self.subscription_product else 'Unknown')
        return f"{self.quantity} of {product_name}"

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        """Sepetteki tüm ürünlerin toplam fiyatını hesapla"""
        total = 0
        for item in self.items.all():
            total += item.get_total_price()
        return total

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    subscription_product = models.ForeignKey('SubscriptionProduct', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def get_total_price(self):
        """Bu cart item'ın toplam fiyatını hesapla"""
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        # Eğer price belirtilmemişse, ürünün güncel fiyatını kullan
        if not self.price:
            if self.product:
                self.price = self.product.price
            elif self.subscription_product:
                if hasattr(self.subscription_product, 'price') and self.subscription_product.price:
                    self.price = self.subscription_product.price
                else:
                    self.price = self.subscription_product.monthly_price
        super().save(*args, **kwargs)

    def __str__(self):
        product_name = self.product.name if self.product else (self.subscription_product.name if self.subscription_product else 'Unknown')
        return f"{self.quantity} of {product_name} in cart"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField() # Assuming 1-5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"

class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return f"Wishlist for {self.user.username}"

class SubscriptionProduct(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Geriye uyumluluk için price field'ını monthly_price ile doldur
        if not self.price:
            self.price = self.monthly_price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
        