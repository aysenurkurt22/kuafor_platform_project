from django.contrib import admin
from .models import MembershipPlan, UserMembership

admin.site.register(MembershipPlan)
admin.site.register(UserMembership)