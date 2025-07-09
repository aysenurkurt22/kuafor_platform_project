from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import MembershipPlan, UserMembership
from django.contrib import messages
from django.utils import timezone
from kuafor_platform_project.utils import award_referral_bonus
from notifications.models import Notification
from django.utils.translation import gettext_lazy as _

def membership_plans_list(request):
    plans = MembershipPlan.objects.all().order_by('price')
    user_membership = None
    if request.user.is_authenticated:
        user_membership = UserMembership.objects.filter(user=request.user, is_active=True).first()
    return render(request, 'memberships/membership_plans_list.html', {'plans': plans, 'user_membership': user_membership})

@login_required
def purchase_membership(request, plan_slug):
    membership_plan = get_object_or_404(MembershipPlan, slug=plan_slug)

    if request.method == 'POST':
        payment_successful = True

        if payment_successful:
            UserMembership.objects.filter(user=request.user, is_active=True).update(is_active=False)

            end_date = None
            if membership_plan.duration_months > 0:
                end_date = timezone.now() + timezone.timedelta(days=30 * membership_plan.duration_months)

            user_membership = UserMembership.objects.create(
                user=request.user,
                membership_plan=membership_plan,
                end_date=end_date,
                is_active=True
            )
            request.user.user_membership = user_membership
            request.user.save()

            if request.user.referred_by:
                award_referral_bonus(request.user.referred_by)
                messages.info(request, _("{referred_by_username} tarafından davet edildiğiniz için referans bonusu kazandınız!").format(referred_by_username=request.user.referred_by.username))

            messages.success(request, _("{plan_type} üyeliğiniz başarıyla aktifleştirildi!").format(plan_type=membership_plan.membership_type))
            Notification.objects.create(
                user=request.user,
                message=_("{plan_name} üyeliğiniz başarıyla başlatıldı.").format(plan_name=membership_plan.name),
                notification_type='MEMBERSHIP_UPDATE',
                related_object_id=user_membership.id
            )
            return redirect('users:user_dashboard')
        else:
            messages.error(request, _('Ödeme başarısız oldu. Lütfen tekrar deneyin.'))
            return redirect('memberships:membership_plans_list')

    return render(request, 'memberships/purchase_membership.html', {'plan': membership_plan})

@login_required
def manage_subscription(request):
    user_membership = get_object_or_404(UserMembership, user=request.user)
    
    if request.method == 'POST':
        auto_renew = request.POST.get('auto_renew') == 'on'
        user_membership.auto_renew = auto_renew
        user_membership.save()
        messages.success(request, _("Üyelik ayarlarınız başarıyla güncellendi."))
        return redirect('memberships:manage_subscription')
    
    context = {
        'user_membership': user_membership,
    }
    return render(request, 'memberships/manage_subscription.html', context)

@login_required
def select_membership_plan(request, plan_type):
    membership_plan = get_object_or_404(MembershipPlan, membership_type=plan_type.upper())
    
    if request.method == 'POST':
        user_membership, created = UserMembership.objects.get_or_create(user=request.user)
        user_membership.membership_plan = membership_plan
        user_membership.is_active = True
        user_membership.start_date = timezone.now()
        
        if membership_plan.membership_type == 'MONTHLY':
            user_membership.end_date = timezone.now() + timezone.timedelta(days=30)
            user_membership.next_renewal_date = user_membership.end_date
        elif membership_plan.membership_type == 'ANNUAL':
            user_membership.end_date = timezone.now() + timezone.timedelta(days=365)
            user_membership.next_renewal_date = user_membership.end_date

        user_membership.last_payment_date = timezone.now()
        user_membership.auto_renew = True
        user_membership.save()

        messages.success(request, _("{plan_name} üyeliğiniz başarıyla başlatıldı!").format(plan_name=membership_plan.name))
        Notification.objects.create(
            user=request.user,
            message=_("{plan_name} üyeliğiniz başarıyla başlatıldı.").format(plan_name=membership_plan.name),
            notification_type='MEMBERSHIP_UPDATE',
            related_object_id=user_membership.id
        )
        return redirect('memberships:manage_subscription')
    
    context = {
        'membership_plan': membership_plan,
    }
    return render(request, 'memberships/select_membership_plan.html', context)
