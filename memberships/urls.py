from django.urls import path
from . import views

urlpatterns = [
    path('plans/', views.membership_plans_list, name='membership_plans_list'),
    path('purchase/<slug:plan_slug>/', views.purchase_membership, name='purchase_membership'),
]