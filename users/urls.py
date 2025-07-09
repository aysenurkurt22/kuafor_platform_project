from django.urls import path, include
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification_email, name='resend_verification_email'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('profile/update/', views.user_profile_update, name='profile_update'),
    
    # Role upgrade URLs
    path('upgrade/employer/', views.upgrade_to_employer, name='upgrade_employer'),
    path('upgrade/seller/', views.upgrade_to_seller, name='upgrade_seller'),  # YENİ
    path('manage/roles/', views.downgrade_role, name='manage_roles'),  # YENİ
    
    # Django'nun hazır auth URL'lerini dahil et
    path('', include('django.contrib.auth.urls')),
]
