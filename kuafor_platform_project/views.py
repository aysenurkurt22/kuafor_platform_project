from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.models import CustomUser
from jobs.models import JobPosting
from shop.models import Product, Order, Cart, CartItem, ProductCategory, Review, Wishlist, SubscriptionProduct
from messaging.models import Message
from notifications.models import Notification
from django.db import transaction
from kuafor_platform_project.utils import send_order_confirmation_email
from django.forms import formset_factory
from shop.forms import CartItemForm, ReviewForm
from django.db.models import Q, Case, When, Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import datetime

def home(request):
    recently_viewed_product_ids = request.session.get('recently_viewed_products', [])
    recently_viewed_products = Product.objects.filter(id__in=recently_viewed_product_ids)
    # Sırayı korumak için manuel sıralama
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(recently_viewed_product_ids)])
    recently_viewed_products = recently_viewed_products.order_by(preserved)

    unread_notifications_count = 0
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'recently_viewed_products': recently_viewed_products,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, 'home.html', context)

@login_required
def analytics_dashboard(request):
    print("Analytics dashboard view accessed!") # Debug print
    if not request.user.is_staff:
        return render(request, '403.html') # Yetkisiz erişim sayfası

    total_users = CustomUser.objects.count()
    total_employers = CustomUser.objects.filter(is_employer=True).count()
    total_customers = CustomUser.objects.filter(is_customer=True).count()
    total_job_postings = JobPosting.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = sum(order.total_amount for order in Order.objects.filter(is_completed=True)) # Sadece tamamlanmış siparişlerden gelir

    # Aylık İş İlanı Trendleri
    job_posting_trends = JobPosting.objects.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
    job_posting_data = [{'month': item['month'].strftime('%Y-%m'), 'count': item['count']} for item in job_posting_trends]

    # Aylık Sipariş ve Gelir Trendleri
    order_trends = Order.objects.annotate(month=TruncMonth('order_date')).values('month').annotate(count=Count('id'), revenue=Sum('total_amount')).order_by('month')
    order_data = [{'month': item['month'].strftime('%Y-%m'), 'count': item['count'], 'revenue': item['revenue']} for item in order_trends]

    # En Çok Satan Ürünler (İlk 5)
    top_selling_products = OrderItem.objects.values('product__name').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity')[:5]

    context = {
        'total_users': total_users,
        'total_employers': total_employers,
        'total_customers': total_customers,
        'total_job_postings': total_job_postings,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'job_posting_data': job_posting_data,
        'order_data': order_data,
        'top_selling_products': top_selling_products,
    }
    return render(request, 'analytics_dashboard.html', context)

def product_list(request, category_slug=None):
    category = None
    categories = ProductCategory.objects.all()
    products = Product.objects.all().order_by('name')
    if category_slug:
        category = get_object_or_404(ProductCategory, slug=category_slug)
        products = products.filter(category=category)
    return render(request, 'shop/product_list.html', {'products': products, 'category': category, 'categories': categories})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # Son görüntülenen ürünleri oturumda sakla
    if 'recently_viewed_products' not in request.session:
        request.session['recently_viewed_products'] = []
    
    recently_viewed = request.session['recently_viewed_products']
    if product.id in recently_viewed:
        recently_viewed.remove(product.id) # Eğer zaten varsa en üste taşı
    recently_viewed.insert(0, product.id) # En yeni görüntüleneni en başa ekle
    request.session['recently_viewed_products'] = recently_viewed[:5] # Sadece son 5 ürünü sakla
    request.session.modified = True

    # Yorumlar
    reviews = product.reviews.all()
    if request.method == 'POST':
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            new_review = review_form.save(commit=False)
            new_review.product = product
            new_review.user = request.user
            try:
                new_review.save()
                messages.success(request, 'Yorumunuz başarıyla eklendi!')
                return redirect('product_detail', pk=pk)
            except Exception as e:
                messages.error(request, f'Yorum eklenirken bir hata oluştu: {e}')
    else:
        review_form = ReviewForm()

    return render(request, 'shop/product_detail.html', {'product': product, 'reviews': reviews, 'review_form': review_form})

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    quantity = int(request.POST.get('quantity', 1)) # Miktar alınıyor

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += quantity # Mevcutsa miktarı artır
    else:
        cart_item.quantity = quantity # Yeni ekleniyorsa miktarı ayarla
    cart_item.save()
    return redirect('cart_detail')

@login_required
def update_cart_item(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete() # Miktar 0 veya daha az ise sil
    return redirect('cart_detail')

@login_required
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_detail')

@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'shop/cart_detail.html', {'cart': cart})

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if request.method == 'POST':
        if cart.items.exists():
            with transaction.atomic():
                # Ödeme başarılı varsayımıyla sipariş oluştur
                order = Order.objects.create(
                    customer=request.user,
                    total_amount=cart.get_total_price(),
                    # shipping_address = request.POST.get('shipping_address', '') # Adres formu eklendiğinde kullanılacak
                )
                for item in cart.items.all():
                    # Ürünün normal ürün mü yoksa abonelik ürünü mü olduğunu kontrol et
                    if item.product:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.product.price
                        )
                        item.product.stock -= item.quantity
                        item.product.save()
                    elif item.subscription_product:
                        OrderItem.objects.create(
                            order=order,
                            subscription_product=item.subscription_product,
                            quantity=item.quantity,
                            price=item.subscription_product.price
                        )
                cart.items.all().delete() # Sepeti boşalt
            send_order_confirmation_email(request.user.email, order.id, order.total_amount) # Sipariş onayı e-postası
            # Bildirim oluştur
            Notification.objects.create(
                user=request.user,
                message=f'Siparişiniz başarıyla alındı! Sipariş No: #{order.id}',
                notification_type='ORDER_UPDATE',
                related_object_id=order.id
            )
            # Burada iyzico ödeme entegrasyonu için yer tutucu olacak
            # Şimdilik başarılı bir ödeme gibi davranıyoruz
            return redirect('order_success') # Başarılı ödeme sonrası yönlendirme
        else:
            return redirect('cart_detail') # Sepet boşsa sepete geri dön
    return render(request, 'shop/checkout.html', {'cart': cart})

def order_success(request):
    return render(request, 'shop/order_success.html')

@login_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user).order_by('-order_date')
    return render(request, 'shop/order_history.html', {'orders': orders})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    return render(request, 'shop/order_detail.html', {'order': order})

def test_view(request):
    print("Test view accessed!")
    return render(request, 'test.html')

def unified_search(request):
    query = request.GET.get('q')
    job_results = []
    product_results = []

    if query:
        # İş ilanlarında arama
        job_results = JobPosting.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(skills_required__icontains=query)
        ).distinct()

        # Ürünlerde arama
        product_results = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) # Kategori adına göre arama
        ).distinct()

    context = {
        'query': query,
        'job_results': job_results,
        'product_results': product_results,
    }
    return render(request, 'search_results.html', context)

@login_required
def add_to_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist.products.add(product)
    messages.success(request, f'{product.name} istek listenize eklendi!')
    return redirect('wishlist_detail')

@login_required
def remove_from_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist.products.remove(product)
    messages.success(request, f'{product.name} istek listenizden kaldırıldı!')
    return redirect('wishlist_detail')

@login_required
def wishlist_detail(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'shop/wishlist.html', {'wishlist': wishlist})

def subscription_product_list(request):
    subscription_products = SubscriptionProduct.objects.filter(is_active=True).order_by('name')
    return render(request, 'shop/subscription_product_list.html', {'subscription_products': subscription_products})

def subscription_product_detail(request, pk):
    subscription_product = get_object_or_404(SubscriptionProduct, pk=pk)
    return render(request, 'shop/subscription_product_detail.html', {'subscription_product': subscription_product})

@login_required
def add_subscription_to_cart(request, pk):
    subscription_product = get_object_or_404(SubscriptionProduct, pk=pk)
    quantity = int(request.POST.get('quantity', 1))

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, subscription_product=subscription_product)
    if not item_created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()
    messages.success(request, f'{subscription_product.name} sepete eklendi!')
    return redirect('cart_detail')
