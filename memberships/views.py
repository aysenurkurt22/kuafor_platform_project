from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import MembershipPlan, UserMembership
from django.contrib import messages
from datetime import datetime, timedelta
from kuafor_platform_project.utils import award_referral_bonus # award_referral_bonus eklendi

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
        # Ödeme işlemi burada gerçekleşecek (şimdilik yer tutucu)
        # Gerçek bir entegrasyon için iyzico API çağrıları buraya gelecek
        payment_successful = True # Simülasyon

        if payment_successful:
            # Mevcut aktif üyeliği pasif yap
            UserMembership.objects.filter(user=request.user, is_active=True).update(is_active=False)

            # Yeni üyelik oluştur
            end_date = None
            if membership_plan.duration_months > 0:
                end_date = datetime.now() + timedelta(days=30 * membership_plan.duration_months)

            user_membership = UserMembership.objects.create(
                user=request.user,
                membership_plan=membership_plan,
                end_date=end_date,
                is_active=True
            )
            request.user.user_membership = user_membership
            request.user.save()

            # Eğer kullanıcı bir referans kodu ile geldiyse, referans verene bonus ver
            if request.user.referred_by:
                award_referral_bonus(request.user.referred_by)
                messages.info(request, f'{request.user.referred_by.username} tarafından davet edildiğiniz için referans bonusu kazandınız!')

            messages.success(request, f'{membership_plan.membership_type} üyeliğiniz başarıyla aktifleştirildi!')
            return redirect('user_dashboard') # Kontrol paneline yönlendir
        else:
            messages.error(request, 'Ödeme başarısız oldu. Lütfen tekrar deneyin.')
            return redirect('membership_plans_list')

    return render(request, 'memberships/purchase_membership.html', {'plan': membership_plan})
