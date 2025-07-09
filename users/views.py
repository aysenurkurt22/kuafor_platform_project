from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, UserPreferencesForm, CustomAuthenticationForm
from kuafor_platform_project.utils import send_welcome_email, award_referral_bonus, send_verification_email
from jobs.models import JobPosting, Application
from shop.models import Order, Product, ProductCategory, OrderItem
from messaging.models import Message
from notifications.models import Notification
from .models import CustomUser
import uuid
from django.db.models import Q, Case, When, Count, Sum
from django.contrib.contenttypes.models import ContentType
from .decorators import employer_required, customer_required
from django.utils.translation import gettext_lazy as _

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account until email is verified
            user.email_verification_token = str(uuid.uuid4())
            user.email = form.cleaned_data['email']
            user.save()
            send_verification_email(request, user)
            messages.success(request, _('Hesabınızı doğrulamak için lütfen e-postanızı kontrol edin.'))
            return redirect('users:login')
        else:
            messages.error(request, _('Lütfen formu doğru şekilde doldurun.'))
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def verify_email(request, token):
    try:
        user = CustomUser.objects.get(email_verification_token=token)
        if not user.email_verified:
            user.email_verified = True
            user.is_active = True
            user.email_verification_token = None  # Clear the token after verification
            user.save()
            messages.success(request, _('E-posta adresiniz başarıyla doğrulandı. Giriş yapabilirsiniz.'))
        else:
            messages.info(request, _('E-posta adresiniz zaten doğrulanmış.'))
    except CustomUser.DoesNotExist:
        messages.error(request, _('Geçersiz doğrulama bağlantısı.'))
    return redirect('users:login')

@login_required
def resend_verification_email(request):
    if request.user.email_verified:
        messages.info(request, _('Hesabınız zaten doğrulanmış.'))
        return redirect('home')
    
    send_verification_email(request, request.user)
    messages.success(request, _('Yeni bir doğrulama e-postası adresinize gönderildi.'))
    return redirect('users:login')

def user_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active and user.email_verified:
                    login(request, user)
                    return redirect('home')
                elif not user.is_active:
                    messages.error(request, _('Hesabınız henüz aktive edilmemiş. Lütfen e-postanızı kontrol edin.'))
                    # Tekrar gönderme linki için context'e kullanıcıyı ekle
                    return render(request, 'users/login.html', {'form': form, 'unverified_user': user})
                else:
                    messages.error(request, _('Giriş başarısız. Lütfen bilgilerinizi kontrol edin.'))
            else:
                messages.error(request, _('Geçersiz kullanıcı adı veya parola.'))
        else:
            messages.error(request, _('Lütfen formu doğru şekilde doldurun.'))
    else:
        form = CustomAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

# User Dashboard
@login_required
def user_dashboard(request):
    user = request.user
    
    # Preferences form'u tanımla - POST request olursa form'u işle
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profil tercihleriniz başarıyla güncellendi.'))
            return redirect('users:user_dashboard')
        else:
            messages.error(request, _('Profil tercihleri güncellenirken bir hata oluştu.'))
    else:
        form = UserPreferencesForm(instance=user)
    
    # Context'i template ile tam uyumlu olacak şekilde hazırla
    context = {
        'user': user,
        'preferences_form': form,
        'user_job_postings': [],
        'user_applications': [],
        'user_orders': [],
        'user_products': [],  # YENİ: Satıcı ürünleri
        'recent_messages': [],
        'recent_notifications': [],
        'recommended_jobs': [],
        'recommended_products': [],
    }

    # Employer için veri hazırla
    if user.is_employer:
        context['user_job_postings'] = JobPosting.objects.filter(employer=user).order_by('-created_at')[:5]
        context['applications'] = Application.objects.filter(job_posting__employer=user).order_by('-application_date')
        context['recommended_jobs'] = JobPosting.objects.exclude(employer=user).order_by('-created_at')[:3]
    
    # Seller için veri hazırla - YENİ
    if user.is_seller:
        # Product modelinde seller field'ı olmadığı için şimdilik boş bırakıyoruz
        # Gelecekte Product modeline seller field eklenebilir
        context['user_products'] = []  # Product.objects.filter(seller=user)[:5] 
    
    # Customer için veri hazırla
    if user.is_customer:
        context['user_orders'] = Order.objects.filter(user=user).order_by('-order_date')[:5]
        context['user_applications'] = Application.objects.filter(applicant=user).order_by('-application_date')[:5]
        context['recommended_products'] = Product.objects.all()[:3]

    # Ortak veriler
    context['recent_messages'] = Message.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-timestamp')[:5]
    context['recent_notifications'] = Notification.objects.filter(user=user).order_by('-timestamp')[:5]

    return render(request, 'users/dashboard.html', context)

@login_required
def user_profile_update(request):
    user = request.user
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profil tercihleriniz başarıyla güncellendi.'))
            return redirect('users:user_dashboard')
        else:
            messages.error(request, _('Profil tercihleri güncellenirken bir hata oluştu.'))
    else:
        form = UserPreferencesForm(instance=user)
    return render(request, 'users/profile_update.html', {'form': form})

@login_required
def upgrade_to_employer(request):
    """Kullanıcıyı employer role'üne yükseltir"""
    if request.method == 'POST':
        user = request.user
        
        if not user.is_employer:
            user.is_employer = True
            
            # Hoş geldin bonusu ver (eğer bu field'lar varsa)
            if hasattr(user, 'job_highlight_credits'):
                user.job_highlight_credits += 3
            if hasattr(user, 'extra_job_posting_credits'):
                user.extra_job_posting_credits += 2
                
            user.save()
            
            # Bildirim oluştur
            Notification.objects.create(
                user=user,
                message='🎉 Tebrikler! İş veren özellikleriniz aktifleştirildi. 3 ücretsiz öne çıkarma kredisi kazandınız!',
                notification_type='ACCOUNT_UPDATE'
            )
            
            messages.success(request, 'Tebrikler! İş veren özellikleriniz başarıyla aktifleştirildi. 3 öne çıkarma kredisi hesabınıza eklendi!')
        else:
            messages.info(request, 'Zaten iş veren özellikleriniz aktif.')
            
        return redirect('users:user_dashboard')
    
    # GET request için onay sayfası
    return render(request, 'users/upgrade_employer.html', {
        'user': request.user
    })

@login_required
def upgrade_to_seller(request):
    """Kullanıcıyı seller role'üne yükseltir"""
    if request.method == 'POST':
        user = request.user
        
        if not user.is_seller:
            user.is_seller = True
            
            # İşletme bilgileri form'dan al (opsiyonel)
            business_name = request.POST.get('business_name', '').strip()
            if business_name:
                user.business_name = business_name
                
            user.save()
            
            # Bildirim oluştur
            Notification.objects.create(
                user=user,
                message='🛍️ Tebrikler! Satıcı özellikleriniz aktifleştirildi. Artık ürün satabilirsiniz.',
                notification_type='ACCOUNT_UPDATE'
            )
            
            messages.success(request, 'Tebrikler! Satıcı özellikleriniz başarıyla aktifleştirildi.')
        else:
            messages.info(request, 'Zaten satıcı özellikleriniz aktif.')
            
        return redirect('users:user_dashboard')
    
    # GET request için onay sayfası
    return render(request, 'users/upgrade_seller.html', {
        'user': request.user
    })

@login_required 
def downgrade_role(request):
    """Kullanıcıların rollerini kapatmasına izin verir"""
    if request.method == 'POST':
        user = request.user
        role_to_remove = request.POST.get('role')
        
        if role_to_remove == 'employer' and user.is_employer:
            user.is_employer = False
            user.save()
            messages.success(request, 'İş veren özellikleriniz kapatıldı.')
            
        elif role_to_remove == 'seller' and user.is_seller:
            user.is_seller = False
            user.save()
            messages.success(request, 'Satıcı özellikleriniz kapatıldı.')
            
        return redirect('users:user_dashboard')
    
    return render(request, 'users/manage_roles.html', {
        'user': request.user
    })

def user_logout(request):
    logout(request)
    messages.info(request, _('Başarıyla çıkış yaptınız.'))
    return redirect('home')

# Decorator test views (for development/testing purposes)
@employer_required
def employer_test_view(request):
    return render(request, 'users/employer_test.html')

@customer_required
def customer_test_view(request):
    return render(request, 'users/customer_test.html')
    