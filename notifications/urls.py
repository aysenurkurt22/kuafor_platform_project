from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.notification_list, name='notification_list'),
    path('mark_as_read/<int:pk>/', views.mark_as_read, name='mark_as_read'),
    path('mark_all_as_read/', views.mark_all_as_read, name='mark_all_as_read'),
]