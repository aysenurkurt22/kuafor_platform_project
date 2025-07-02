from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Cart, CartItem, Order, OrderItem, ProductCategory, Review, Wishlist, SubscriptionProduct
from django.db import transaction
from kuafor_platform_project.utils import send_order_confirmation_email
from django.forms import formset_factory
from shop.forms import CartItemForm, ReviewForm
from django.db.models import Q, Case, When
from notifications.models import Notification
from django.contrib import messages
from django.conf import settings
import requests
import json
from users.models import CustomUser # CustomUser import edildi

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

    context = {
        'total_users': total_users,
        'total_employers': total_employers,
        'total_customers': total_customers,
        'total_job_postings': total_job_postings,
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
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

    # Kullanıcının tercih edilen ürün kategorilerini güncelle
    if request.user.is_authenticated and product.category:
        user = request.user
        current_categories = set(user.preferred_product_categories.split(',')) if user.preferred_product_categories else set()
        new_category = product.category.name.strip()
        if new_category and new_category not in current_categories:
            current_categories.add(new_category)
            user.preferred_product_categories = ', '.join(sorted(list(current_categories)))
            user.save()

    # Üyelik indirimi hesapla
    discounted_price = product.price
    if request.user.is_authenticated and request.user.user_membership and request.user.user_membership.is_active:
        discount_percentage = request.user.user_membership.membership_plan.product_discount_percentage
        discounted_price = product.price * (1 - discount_percentage / 100)

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

    return render(request, 'shop/product_detail.html', {'product': product, 'reviews': reviews, 'review_form': review_form, 'discounted_price': discounted_price})

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    quantity = int(request.POST.get('quantity', 1)) # Miktar alınıyor

    # Üyelik indirimi hesapla
    price_at_purchase = product.price
    if request.user.is_authenticated and request.user.user_membership and request.user.user_membership.is_active:
        discount_percentage = request.user.user_membership.membership_plan.product_discount_percentage
        price_at_purchase = product.price * (1 - discount_percentage / 100)

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += quantity # Mevcutsa miktarı artır
    else:
        cart_item.quantity = quantity # Yeni ekleniyorsa miktarı ayarla
    cart_item.price = price_at_purchase # İndirimli fiyatı kaydet
    cart_item.save()
    return redirect('cart_detail')

@login_required
def update_cart_item(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            # Miktar güncellendiğinde fiyatı tekrar hesaplamaya gerek yok, çünkü price_at_purchase zaten kaydedildi
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
    total_discount = 0
    if request.user.is_authenticated and request.user.user_membership and request.user.user_membership.is_active:
        discount_percentage = request.user.user_membership.membership_plan.product_discount_percentage
        for item in cart.items.all():
            if item.product: # Sadece normal ürünler için indirim
                original_price = item.product.price
                discounted_price = original_price * (1 - discount_percentage / 100)
                total_discount += (original_price - discounted_price) * item.quantity

    return render(request, 'shop/cart_detail.html', {'cart': cart, 'total_discount': total_discount})

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    total_discount = 0
    if request.user.is_authenticated and request.user.user_membership and request.user.user_membership.is_active:
        discount_percentage = request.user.user_membership.membership_plan.product_discount_percentage
        for item in cart.items.all():
            if item.product: # Sadece normal ürünler için indirim
                original_price = item.product.price
                discounted_price = original_price * (1 - discount_percentage / 100)
                total_discount += (original_price - discounted_price) * item.quantity

    # Sadakat puanı kullanımı
    loyalty_points_applied = 0
    loyalty_discount_amount = 0
    if request.method == 'POST' and 'use_loyalty_points' in request.POST and request.user.loyalty_points > 0:
        # Her 100 puan için 1 TL indirim varsayalım
        points_to_use = request.user.loyalty_points
        loyalty_discount_amount = min(points_to_use / 100, (cart.get_total_price() - total_discount)) # Toplam tutarı aşmasın
        loyalty_points_applied = int(loyalty_discount_amount * 100)
        messages.info(request, f'{loyalty_points_applied} sadakat puanı kullanıldı ve ₺{loyalty_discount_amount|floatformat:2} indirim uygulandı.')

    if request.method == 'POST':
        if cart.items.exists():
            with transaction.atomic():
                final_total_amount = cart.get_total_price() - total_discount - loyalty_discount_amount
                if final_total_amount < 0: # Negatif olmaması için kontrol
                    final_total_amount = 0

                order = Order.objects.create(
                    customer=request.user,
                    total_amount=final_total_amount,
                    # shipping_address = request.POST.get('shipping_address', '') # Adres formu eklendiğinde kullanılacak
                )
                for item in cart.items.all():
                    # Ürünün normal ürün mü yoksa abonelik ürünü mü olduğunu kontrol et
                    if item.product:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.price # CartItem'daki indirimli fiyatı kullan
                        )
                        item.product.stock -= item.quantity
                        item.product.save()
                    elif item.subscription_product:
                        OrderItem.objects.create(
                            order=order,
                            subscription_product=item.subscription_product,
                            quantity=item.quantity,
                            price=item.price # CartItem'daki fiyatı kullan
                        )
                # Sadakat puanı kazandır
                loyalty_points_earned = int(order.total_amount / 10) # Her 10 TL için 1 puan
                request.user.loyalty_points += loyalty_points_earned
                
                # Kullanılan sadakat puanlarını düş
                request.user.loyalty_points -= loyalty_points_applied
                request.user.save()
                messages.success(request, f'Siparişiniz için {loyalty_points_earned} sadakat puanı kazandınız!')

                cart.items.all().delete() # Sepeti boşalt
            send_order_confirmation_email(request.user.email, order.id, order.total_amount) # Sipariş onayı e-postası
            # Bildirim oluştur
            Notification.objects.create(
                user=request.user,
                message=f'Siparişiniz başarıyla alındı! Sipariş No: #{order.id}',
                notification_type='ORDER_UPDATE',
                related_object_id=order.id
            )
            # Iyzico ödeme başlatma (yer tutucu)
            iyzico_payment_url = f"{settings.IYZICO_BASE_URL}/payment/auth?conversationId={order.id}" # Örnek URL
            return redirect(iyzico_payment_url)
        else:
            return redirect('cart_detail') # Sepet boşsa sepete geri dön
    return render(request, 'shop/checkout.html', {'cart': cart, 'total_discount': total_discount, 'loyalty_discount_amount': loyalty_discount_amount})

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
    cart_item.price = subscription_product.price # Abonelik ürününün fiyatını kaydet
    cart_item.save()
    messages.success(request, f'{subscription_product.name} sepete eklendi!')
    return redirect('cart_detail')

def iyzico_callback(request):
    # Iyzico'dan gelen geri bildirimleri işleme
    # Bu kısım, Iyzico'nun ödeme tamamlandıktan sonra yönlendirdiği URL olacaktır.
    # Genellikle, Iyzico'dan gelen POST verilerini doğrulamak ve sipariş durumunu güncellemek gerekir.
    # Şimdilik basit bir başarı/hata mesajı gösteriyoruz.
    if request.method == 'POST':
        # Örnek: Iyzico'dan gelen verileri logla
        print("Iyzico Callback Data:", request.POST)
        # Gerçek entegrasyonda, burada Iyzico API'si ile ödeme durumunu sorgulayabiliriz.
        # Örneğin, paymentId veya conversationId kullanarak.
        # if payment_successful:
        #     order = Order.objects.get(id=conversationId)
        #     order.status = 'PROCESSING'
        #     order.is_completed = True
        #     order.save()
        messages.success(request, 'Ödeme işlemi Iyzico tarafından başarıyla tamamlandı!')
        return redirect('order_success')
    else:
        messages.error(request, 'Ödeme işlemi sırasında bir hata oluştu veya iptal edildi.')
        return redirect('cart_detail')
