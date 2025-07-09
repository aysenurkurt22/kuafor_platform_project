from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('', views.contact_us, name='contact_us'),
    path('report/<int:content_type_id>/<int:object_id>/', views.report_content, name='report_content'),
]
