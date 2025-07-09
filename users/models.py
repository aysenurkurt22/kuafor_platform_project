from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_employer = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)  # YENİ: Satıcı rolü
    
    user_membership = models.OneToOneField('memberships.UserMembership', on_delete=models.SET_NULL, null=True, blank=True)
    loyalty_points = models.IntegerField(default=0)
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    job_highlight_credits = models.IntegerField(default=0)
    extra_job_posting_credits = models.IntegerField(default=0)
    
    # YENİ: Business fields (satıcılar için)
    business_name = models.CharField(max_length=200, blank=True, null=True, help_text="İşletme adı")
    tax_number = models.CharField(max_length=50, blank=True, null=True, help_text="Vergi numarası")
    seller_verified = models.BooleanField(default=False, help_text="Satıcı doğrulaması")
    
    preferred_locations = models.TextField(blank=True, null=True, help_text="Virgülle ayrılmış tercih edilen lokasyonlar")
    preferred_skills = models.TextField(blank=True, null=True, help_text="Virgülle ayrılmış tercih edilen yetenekler")
    preferred_product_categories = models.TextField(blank=True, null=True, help_text="Virgülle ayrılmış tercih edilen ürün kategorileri")
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True, unique=True)

    def __str__(self):
        return self.username
        