from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('test/', views.test_view, name='test_view'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('', views.home, name='home'),
    path('users/', include('users.urls')),
    path('jobs/', include('jobs.urls')),
    path('shop/', include('shop.urls')),
    path('memberships/', include('memberships.urls')),
    path('search/', views.unified_search, name='unified_search'),
    path('contact/', include('contact.urls')),
    path('pages/', include('pages.urls')),
    path('education/', include('education.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)