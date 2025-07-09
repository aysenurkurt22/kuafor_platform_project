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
from users.models import CustomUser
from users.decorators import customer_required, employer_required # Decorators import edildi
import logging
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

def home(request):
    recently_viewed_product_ids = request.session.get('recently_viewed_products', [])
    recently_viewed_products = Product.objects.filter(id__in=recently_viewed_product_ids)
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
    if not request.user.is_staff:
        return render(request, '403.html')
    total_users = CustomUser.objects.count()
    total_employers = CustomUser.objects.filter(is_employer=True).count()
    total_customers = CustomUser.objects.filter(is_customer=True).count()
    total_job_postings = JobPosting.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = sum(order.total_amount for order in Order.objects.filter(is_completed=True))
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
    products_query = Product.objects.filter(is_active=True).order_by('name')
    if category_slug:
        category = get_object_or_404(ProductCategory, slug=category_slug)
        products_query = products_query.filter(category=category)
    query_q = request.GET.get('q')
    min_price_q = request.GET.get('min_price')
    max_price_q = request.GET.get('max_price')
    if query_q:
        products_query = products_query.filter(Q(name__icontains=query_q) | Q(description__icontains=query_q))
    if min_price_q:
        products_query = products_query.filter(price__gte=min_price_q)
    if max_price_q:
        products_query = products_query.filter(price__lte=max_price_q)
    context = {
        'products': products_query,
        'category': category,
        'categories': categories,
        'selected_q': query_q,
        'selected_min_price': min_price_q,
        'selected_max_price': max_price_q,
    }
    return render(request, 'shop/product_list.html', context)

from django.contrib.contenttypes.models import ContentType

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # ... (rest of the view) ...
    content_type_id = ContentType.objects.get_for_model(product).id
    context = {
        'product': product,
        'reviews': reviews,
        'review_form': review_form,
        'discounted_price': discounted_price,
        'content_type_id': content_type_id,
    }
    return render(request, 'shop/product_detail.html', context)


@login_required
@customer_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    quantity = int(request.POST.get('quantity', 1))

    if quantity > product.stock:
        messages.error(request, f"'{product.name}' için stokta yeterli ürün bulunmamaktadır. En fazla {product.stock} adet ekleyebilirsiniz.")
        return redirect('shop:product_detail', pk=pk)

    price_at_purchase = product.price
    if request.user.is_authenticated and request.user.user_membership and request.user.user_membership.is_active:
        discount_percentage = request.user.user_membership.membership_plan.product_discount_percentage
        price_at_purchase = product.price * (1 - discount_percentage / 100)

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'price': price_at_purchase})
    
    if not item_created:
        if cart_item.quantity + quantity > product.stock:
            messages.error(request, f"Sepetinizdeki miktar ile birlikte '{product.name}' için stok aşıldı. Sepetinizde {cart_item.quantity} adet var, en fazla {product.stock - cart_item.quantity} adet daha ekleyebilirsiniz.")
            return redirect('shop:product_detail', pk=pk)
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    
    cart_item.save()
    messages.success(request, f"{quantity} adet '{product.name}' sepete eklendi.")
    return redirect('shop:cart_detail')

@login_required
@customer_required
def update_cart_item(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('shop:cart_detail')

@login_required
@customer_required
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    cart_item.delete()
    return redirect('shop:cart_detail')

@login_required
@customer_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    total_discount = 0
    if request.user.is_authenticated and request.user.user_membership and request.user.user_membership.is_active:
        discount_percentage = request.user.user_membership.membership_plan.product_discount_percentage
        for item in cart.items.all():
            if item.product:
                original_price = item.product.price
                discounted_price = original_price * (1 - discount_percentage / 100)
                total_discount += (original_price - discounted_price) * item.quantity
    final_amount = cart.get_total_price() - total_discount

    # Context'e final_amount'u ekle
    context = {
        'cart': cart,
        'total_discount': total_discount,
        'final_amount': final_amount,
        }
    return render(request, 'shop/cart_detail.html', context)

@login_required
@customer_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    total_discount = 0
    if request.user.is_authenticated and request.user.user_membership and request.user.user_membership.is_active:
        discount_percentage = request.user.user_membership.membership_plan.product_discount_percentage
        for item in cart.items.all():
            if item.product:
                original_price = item.product.price
                discounted_price = original_price * (1 - discount_percentage / 100)
                total_discount += (original_price - discounted_price) * item.quantity
    loyalty_points_applied = 0
    loyalty_discount_amount = 0
    if request.method == 'POST' and 'use_loyalty_points' in request.POST and request.user.loyalty_points > 0:
        points_to_use = request.user.loyalty_points
        loyalty_discount_amount = min(points_to_use / 100, (cart.get_total_price() - total_discount))
        loyalty_points_applied = int(loyalty_discount_amount * 100)
        messages.info(request, f'{loyalty_points_applied} sadakat puanı kullanıldı ve ₺{loyalty_discount_amount|floatformat:2} indirim uygulandı.')
    if request.method == 'POST':
        if cart.items.exists():
            with transaction.atomic():
                final_total_amount = cart.get_total_price() - total_discount - loyalty_discount_amount
                if final_total_amount < 0:
                    final_total_amount = 0
                order = Order.objects.create(customer=request.user, total_amount=final_total_amount)
                for item in cart.items.all():
                    if item.product:
                        OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.price)
                        item.product.stock -= item.quantity
                        item.product.save()
                    elif item.subscription_product:
                        OrderItem.objects.create(order=order, subscription_product=item.subscription_product, quantity=item.quantity, price=item.price)
                loyalty_points_earned = int(order.total_amount / 10)
                request.user.loyalty_points += loyalty_points_earned
                request.user.loyalty_points -= loyalty_points_applied
                request.user.save()
                messages.success(request, f'Siparişiniz için {loyalty_points_earned} sadakat puanı kazandınız!')
                cart.items.all().delete()
            send_order_confirmation_email(request.user.email, order.id, order.total_amount)
            Notification.objects.create(user=request.user, message=f'Siparişiniz başarıyla alındı! Sipariş No: #{order.id}', notification_type='ORDER_UPDATE', related_object_id=order.id)
            messages.info(request, "Ödeme işlemi Iyzico'ya yönlendiriliyor...")
            return redirect('shop:iyzico_initiate_payment', order_id=order.id) # Yeni bir view'a yönlendir
        else:
            return redirect('shop:cart_detail')
    return render(request, 'shop/checkout.html', {'cart': cart,'total_discount': total_discount, 'loyalty_discount_amount': loyalty_discount_amount})

@login_required
@customer_required
def iyzico_initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    # Iyzico API çağrısı için gerekli parametreleri hazırla
    # Bu kısım Iyzico dokümantasyonuna göre doldurulmalıdır.
    # Örnek olarak, sadece temel bir yapı gösterilmiştir.
    try:
        # Iyzico API'sine gönderilecek veriler
        request_data = {
            'locale': 'tr',
            'conversationId': str(order.id),
            'price': str(order.total_amount),
            'paidPrice': str(order.total_amount),
            'currency': 'TL',
            'basketId': str(order.id),
            'paymentGroup': 'PRODUCT',
            'buyer': {
                'id': str(request.user.id),
                'name': request.user.first_name or request.user.username,
                'surname': request.user.last_name or '',
                'gsmNumber': '+905xxxxxxxx', # Gerçek telefon numarası
                'email': request.user.email,
                'identityNumber': '11111111111', # Gerçek kimlik numarası
                'lastLoginDate': '2023-01-01 10:00:00', # Örnek tarih
                'registrationDate': order.customer.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                'registrationAddress': 'N/A', # Gerçek adres
                'ip': request.META.get('REMOTE_ADDR', '127.0.0.1'),
                'city': 'Istanbul', # Gerçek şehir
                'country': 'Turkey', # Gerçek ülke
                'zipCode': '34000', # Gerçek posta kodu
            },
            'shippingAddress': {
                'contactName': request.user.first_name + " " + request.user.last_name if request.user.first_name and request.user.last_name else request.user.username,
                'city': 'Istanbul', # Gerçek şehir
                'country': 'Turkey', # Gerçek ülke
                'address': order.shipping_address or 'N/A', # Gerçek adres
                'zipCode': '34000', # Gerçek posta kodu
            },
            'billingAddress': {
                'contactName': request.user.first_name + " " + request.user.last_name if request.user.first_name and request.user.last_name else request.user.username,
                'city': 'Istanbul', # Gerçek şehir
                'country': 'Turkey', # Gerçek ülke
                'address': order.shipping_address or 'N/A', # Gerçek adres
                'zipCode': '34000', # Gerçek posta kodu
            },
            'basketItems': [],
        }

        for item in order.items.all():
            product_name = item.product.name if item.product else item.subscription_product.name
            item_category = item.product.category.name if item.product and item.product.category else 'Diğer'
            request_data['basketItems'].append({
                'id': str(item.id),
                'name': product_name,
                'category1': item_category,
                'itemType': 'PHYSICAL' if item.product else 'VIRTUAL',
                'price': str(item.price),
                'quantity': item.quantity,
            })

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {settings.IYZICO_API_KEY}', # Bu kısım Iyzico'nun kendi imzalama mekanizmasına göre değişebilir
            'x-api-key': settings.IYZICO_API_KEY, # Genellikle bu şekilde olmaz, Iyzico'nun kendi auth header'ı vardır
            'x-secret-key': settings.IYZICO_SECRET_KEY, # Genellikle bu şekilde olmaz
        }

        # Iyzico API endpoint'i (gerçek endpoint Iyzico dokümantasyonunda bulunmalı)
        iyzico_api_url = f"{settings.IYZICO_BASE_URL}/payment/auth"
        
        # Bu kısım Iyzico'nun gerçek API çağrısı ve yanıtına göre değişecektir.
        # Genellikle bir POST isteği ile ödeme başlatılır ve bir redirect URL alınır.
        # Burada sadece bir yer tutucu olarak gösterilmiştir.
        response = requests.post(iyzico_api_url, headers=headers, data=json.dumps(request_data))
        response.raise_for_status() # HTTP hataları için istisna fırlat
        response_data = response.json()

        if response_data.get('status') == 'success' and response_data.get('paymentPageUrl'):
            return redirect(response_data['paymentPageUrl'])
        else:
            logger.error(f"Iyzico ödeme başlatma hatası: {response_data.get('errorMessage', 'Bilinmeyen Hata')}")
            messages.error(request, 'Ödeme başlatılırken bir hata oluştu. Lütfen tekrar deneyin.')
            return redirect('shop:checkout')

    except requests.exceptions.RequestException as e:
        logger.error(f"Iyzico API bağlantı hatası: {e}")
        messages.error(request, 'Ödeme servisine bağlanırken bir hata oluştu. Lütfen daha sonra tekrar deneyin.')
        return redirect('shop:checkout')
    except Exception as e:
        logger.error(f"Beklenmedik bir hata oluştu: {e}")
        messages.error(request, 'Beklenmedik bir hata oluştu. Lütfen tekrar deneyin.')
        return redirect('shop:checkout')


def iyzico_callback(request):
    # Iyzico'dan gelen callback verilerini işle
    # Bu kısım Iyzico dokümantasyonuna göre doldurulmalıdır.
    # Genellikle POST ile gelen veriler doğrulanır ve ödeme durumu güncellenir.
    logger.info(f"Iyzico Callback Received: {request.POST.dict()}")
    
    # Örnek: Iyzico'dan gelen conversationId ile siparişi bul
    conversation_id = request.POST.get('conversationId')
    if conversation_id:
        try:
            order = Order.objects.get(id=conversation_id)
            # Iyzico'dan gelen ödeme durumunu kontrol et
            # Bu kısım Iyzico'nun callback verilerine göre değişir.
            payment_status = request.POST.get('paymentStatus') # Örnek bir alan
            
            if payment_status == 'SUCCESS': # Başarılı ödeme
                order.status = 'COMPLETED'
                order.is_completed = True
                order.save()
                messages.success(request, 'Ödeme başarıyla tamamlandı ve siparişiniz onaylandı!')
                Notification.objects.create(user=order.customer, message=f'Siparişiniz başarıyla tamamlandı! Sipariş No: #{order.id}', notification_type='ORDER_UPDATE', related_object_id=order.id)
                return redirect('shop:order_success')
            else:
                order.status = 'FAILED'
                order.save()
                messages.error(request, 'Ödeme işlemi başarısız oldu veya iptal edildi.')
                Notification.objects.create(user=order.customer, message=f'Siparişiniz için ödeme başarısız oldu. Sipariş No: #{order.id}', notification_type='ORDER_UPDATE', related_object_id=order.id)
                return redirect('shop:checkout') # Ödeme başarısızsa tekrar ödeme sayfasına yönlendir
        except Order.DoesNotExist:
            logger.error(f"Iyzico Callback: Sipariş bulunamadı: {conversation_id}")
            messages.error(request, 'Geçersiz sipariş bilgisi.')
            return redirect('home')
    else:
        logger.warning("Iyzico Callback: conversationId eksik.")
        messages.error(request, 'Ödeme bilgileri eksik.')
        return redirect('home')

@login_required
@customer_required
def generate_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    return render(request, 'shop/invoice.html', {'order': order})

def order_success(request):
    return render(request, 'shop/order_success.html')

@login_required
@customer_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user).order_by('-order_date')
    return render(request, 'shop/order_history.html', {'orders': orders})

@login_required
@customer_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    return render(request, 'shop/order_detail.html', {'order': order})

def test_view(request):
    return render(request, 'test.html')

def unified_search(request):
    query = request.GET.get('q')
    job_results = []
    product_results = []
    if query:
        job_results = JobPosting.objects.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query) | Q(skills_required__icontains=query)).distinct()
        product_results = Product.objects.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query)).distinct()
    context = {'query': query, 'job_results': job_results, 'product_results': product_results}
    return render(request, 'search_results.html', context)

@login_required
@customer_required
def add_to_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist.products.add(product)
    messages.success(request, f'{product.name} istek listenize eklendi!')
    return redirect('shop:wishlist_detail')

@login_required
@customer_required
def remove_from_wishlist(request, pk):
    product = get_object_or_404(Product, pk=pk)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist.products.remove(product)
    messages.success(request, f'{product.name} istek listenizden kaldırıldı!')
    return redirect('shop:wishlist_detail')

@login_required
@customer_required
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
@customer_required
def add_subscription_to_cart(request, pk):
    subscription_product = get_object_or_404(SubscriptionProduct, pk=pk)
    quantity = int(request.POST.get('quantity', 1))
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, subscription_product=subscription_product)
    if not item_created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.price = subscription_product.price
    cart_item.save()
    messages.success(request, f'{subscription_product.name} sepete eklendi!')
    return redirect('shop:cart_detail')

def iyzico_callback(request):
    if request.method == 'POST':
        print("Iyzico Callback Data:", request.POST)
        messages.success(request, 'Ödeme işlemi Iyzico tarafından başarıyla tamamlandı!')
        return redirect('order_success')
    else:
        messages.error(request, 'Ödeme işlemi sırasında bir hata oluştu veya iptal edildi.')
        return redirect('cart_detail')