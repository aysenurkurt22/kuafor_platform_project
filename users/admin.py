from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_staff', 'is_employer', 'is_customer']
    fieldsets = UserAdmin.fieldsets + (('User Roles', {'fields': ('is_employer', 'is_customer')}),)

admin.site.register(CustomUser, CustomUserAdmin)