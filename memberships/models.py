from django.db import models
from django.conf import settings

class MembershipPlan(models.Model):
    PLAN_CHOICES = (
        ('FREE', 'Free'),
        ('BASIC', 'Basic'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    )
    slug = models.SlugField(null=True, blank=True)
    membership_type = models.CharField(choices=PLAN_CHOICES, default='FREE', max_length=30)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    duration_months = models.IntegerField(default=1)
    max_job_postings = models.IntegerField(default=1)
    highlight_listings = models.BooleanField(default=False)
    featured_listings = models.BooleanField(default=False)
    cv_pool_access = models.BooleanField(default=False)
    analytics_access = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    custom_integrations = models.BooleanField(default=False)
    product_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00) # Yeni indirim alanı

    def __str__(self):
        return self.membership_type

class UserMembership(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    membership_plan = models.ForeignKey(MembershipPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.username} - {self.membership_plan.membership_type}'