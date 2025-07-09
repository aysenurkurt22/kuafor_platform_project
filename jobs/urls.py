from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('post/', views.job_post_create, name='job_post_create'),
    path('browse/', views.job_post_list, name='job_post_list'),
    path('job/<int:pk>/', views.job_post_detail, name='job_post_detail'),
    path('job/<int:pk>/highlight/', views.highlight_job_post, name='highlight_job_post'),
    path('job/<int:pk>/apply/', views.apply_job, name='apply_job'),
    path('applications/', views.manage_applications, name='manage_applications'),
    path('application/<int:pk>/update/', views.update_application_status, name='update_application_status'),
]
