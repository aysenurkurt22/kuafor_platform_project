from django.urls import path
from . import views

app_name = 'memberships'

urlpatterns = [
    path('plans/', views.membership_plans_list, name='membership_plans_list'),
    path('purchase/<slug:plan_slug>/', views.purchase_membership, name='purchase_membership'),
    path('manage/', views.manage_subscription, name='manage_subscription'),
    path('select_plan/<str:plan_type>/', views.select_membership_plan, name='select_membership_plan'),
]