from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, UserPreferencesForm
from kuafor_platform_project.utils import send_welcome_email, award_referral_bonus
from jobs.models import JobPosting, Application
from shop.models import Order, Product, ProductCategory, OrderItem
from messaging.models import Message
from notifications.models import Notification
from .models import CustomUser
import uuid
from django.db.models import Q, Case, When, Count, Sum

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Benzersiz referans kodu oluştur
            user.referral_code = str(uuid.uuid4())[:8].upper()

            # Referans kodu ile gelen kullanıcıyı ata
            referred_by_code = request.GET.get('ref')
            if referred_by_code:
                try:
                    referrer = CustomUser.objects.get(referral_code=referred_by_code)
                    user.referred_by = referrer
                    # Referans bonusunu ödüllendir
                    award_referral_bonus(referrer)
                    messages.success(request, f'{referrer.username} tarafından davet edildiniz ve bonus kazandınız!')
                except CustomUser.DoesNotExist:
                    messages.warning(request, 'Geçersiz referans kodu.')

            user.save()
            login(request, user)
            send_welcome_email(user.email, user.username)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
        else:
            print(form.errors)
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def user_dashboard(request):
    user_job_postings = []
    user_orders = []
    recent_messages = []
    recent_notifications = []
    recommended_jobs = []
    recommended_products = []
    user_applications = []

    if request.method == 'POST':
        preferences_form = UserPreferencesForm(request.POST, instance=request.user)
        if preferences_form.is_valid():
            preferences_form.save()
            messages.success(request, 'Tercihleriniz başarıyla güncellendi!')
            return redirect('user_dashboard')
        else:
            messages.error(request, 'Tercihler güncellenirken bir hata oluştu.')
    else:
        preferences_form = UserPreferencesForm(instance=request.user)

    if request.user.is_employer:
        user_job_postings = JobPosting.objects.filter(employer=request.user).order_by('-created_at')[:5]
        
        # İşverenler için önerilen iş ilanları (kendi ilanları hariç, tercihlere ve popülerliğe göre)
        recommended_jobs_query = JobPosting.objects.exclude(employer=request.user).filter(is_active=True)
        
        # Tercih edilen lokasyonlara göre filtrele
        if request.user.preferred_locations:
            locations = [loc.strip() for loc in request.user.preferred_locations.split(',') if loc.strip()]
            if locations:
                q_objects = Q()
                for loc in locations:
                    q_objects |= Q(location__icontains=loc)
                recommended_jobs_query = recommended_jobs_query.filter(q_objects)
        
        # Tercih edilen yeteneklere göre filtrele
        if request.user.preferred_skills:
            skills = [skill.strip() for skill in request.user.preferred_skills.split(',') if skill.strip()]
            if skills:
                q_objects = Q()
                for skill in skills:
                    q_objects |= Q(skills_required__icontains=skill)
                recommended_jobs_query = recommended_jobs_query.filter(q_objects)
        
        # Popülerliğe göre sırala (örneğin, en çok görüntülenenler veya başvurulanlar)
        # Şimdilik en yenilerle birleştiriyoruz, daha gelişmiş bir sistem için ayrı bir metrik gerekebilir.
        recommended_jobs = recommended_jobs_query.order_by('-created_at')[:5]
    
    if request.user.is_customer:
        user_orders = Order.objects.filter(customer=request.user).order_by('-order_date')[:5]
        user_applications = Application.objects.filter(applicant=request.user).order_by('-application_date')[:5]

        # Müşteriler için önerilen ürünler (tercihlere, satın alma geçmişine ve popülerliğe göre)
        recommended_products_query = Product.objects.all()
        
        # Tercih edilen ürün kategorilerine göre filtrele
        if request.user.preferred_product_categories:
            categories = [cat.strip() for cat in request.user.preferred_product_categories.split(',') if cat.strip()]
            if categories:
                q_objects = Q()
                for cat in categories:
                    q_objects |= Q(category__name__icontains=cat)
                recommended_products_query = recommended_products_query.filter(q_objects)
        
        # Satın alma geçmişindeki kategorilere göre öneri
        purchased_categories = OrderItem.objects.filter(order__customer=request.user, product__isnull=False).values_list('product__category__name', flat=True).distinct()
        if purchased_categories:
            q_objects = Q()
            for cat_name in purchased_categories:
                if cat_name: # None olmayan kategorileri filtrele
                    q_objects |= Q(category__name__icontains=cat_name)
            recommended_products_query = recommended_products_query.filter(q_objects)

        # Popülerliğe göre sırala (örneğin, en çok satanlar)
        # Şimdilik en yenilerle birleştiriyoruz.
        recommended_products = recommended_products_query.order_by('-created_at')[:5]

        # Başvurulan iş ilanlarının lokasyon ve yeteneklerine göre iş ilanı önerileri (müşteriler için)
        applied_job_locations = Application.objects.filter(applicant=request.user).values_list('job_posting__location', flat=True).distinct()
        applied_job_skills = Application.objects.filter(applicant=request.user).values_list('job_posting__skills_required', flat=True).distinct()

        recommended_jobs_for_customer_query = JobPosting.objects.filter(is_active=True)
        if applied_job_locations:
            q_objects = Q()
            for loc in applied_job_locations:
                if loc: 
                    q_objects |= Q(location__icontains=loc)
            recommended_jobs_for_customer_query = recommended_jobs_for_customer_query.filter(q_objects)
        if applied_job_skills:
            q_objects = Q()
            for skill_str in applied_job_skills:
                if skill_str: 
                    for skill in skill_str.split(','):
                        q_objects |= Q(skills_required__icontains=skill.strip())
            recommended_jobs_for_customer_query = recommended_jobs_for_customer_query.filter(q_objects)
        recommended_jobs = recommended_jobs_for_customer_query.order_by('-created_at')[:5]

    recent_messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')[:5]
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:5]

    context = {
        'user_job_postings': user_job_postings,
        'user_orders': user_orders,
        'user_applications': user_applications,
        'recent_messages': recent_messages,
        'recent_notifications': recent_notifications,
        'recommended_jobs': recommended_jobs,
        'recommended_products': recommended_products,
        'preferences_form': preferences_form,
    }
    return render(request, 'users/dashboard.html', context)