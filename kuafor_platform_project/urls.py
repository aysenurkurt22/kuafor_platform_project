"""
URL configuration for kuafor_platform_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views # Bu satırı ekledik

urlpatterns = [
    path('admin/', admin.site.urls),
    path('test/', views.test_view, name='test_view'), # Test URL'si
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('', views.home, name='home'), # Ana sayfa
    path('users/', include('users.urls')),
    path('jobs/', include('jobs.urls')),
    path('shop/', include('shop.urls')),
    path('search/', views.unified_search, name='unified_search'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
