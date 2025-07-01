from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from kuafor_platform_project.utils import send_welcome_email
from jobs.models import JobPosting
from shop.models import Order, Product
from messaging.models import Message
from notifications.models import Notification

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            send_welcome_email(user.email, user.username) # Welcome email
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
            # Form geçerli değilse, hata mesajlarını konsola yazdır
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

    if request.user.is_employer:
        user_job_postings = JobPosting.objects.filter(employer=request.user).order_by('-created_at')[:5]
        # İşverenler için önerilen iş ilanları (kendi ilanları hariç en yeniler)
        recommended_jobs = JobPosting.objects.exclude(employer=request.user).order_by('-created_at')[:3]
    
    if request.user.is_customer:
        user_orders = Order.objects.filter(customer=request.user).order_by('-order_date')[:5]
        # Müşteriler için önerilen ürünler (en yeniler)
        recommended_products = Product.objects.all().order_by('-created_at')[:3]

    recent_messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')[:5]
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:5]

    context = {
        'user_job_postings': user_job_postings,
        'user_orders': user_orders,
        'recent_messages': recent_messages,
        'recent_notifications': recent_notifications,
        'recommended_jobs': recommended_jobs,
        'recommended_products': recommended_products,
    }
    return render(request, 'users/dashboard.html', context)