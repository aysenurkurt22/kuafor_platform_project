from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from notifications.models import Notification # Notification import edildi

def send_verification_email(request, user):
    token = user.email_verification_token
    subject = 'Hesabınızı Doğrulayın - Kuaför Kariyer Platformu'
    verification_url = request.build_absolute_uri(
        reverse('users:verify_email', kwargs={'token': token})
    )
    message = f"""
    Merhaba {user.username},

    Kuaför Kariyer Platformu'na kaydınızı tamamlamak için lütfen aşağıdaki linke tıklayın:
    {verification_url}

    Eğer bu isteği siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.

    Saygılarımızla,
    Kuaför Kariyer Ekibi
    """
    html_message = render_to_string('emails/verify_email.html', {
        'username': user.username,
        'verification_url': verification_url,
    })
    from_email = settings.EMAIL_HOST_USER if settings.EMAIL_HOST_USER else 'noreply@kuaforplatform.com'
    send_mail(subject, message, from_email, [user.email], html_message=html_message, fail_silently=False)


def send_welcome_email(user_email, username):
    subject = 'Kuaför Kariyer & E-Commerce Platformuna Hoş Geldiniz!'
    message = f'Merhaba {username},\n\nPlatformumuza hoş geldiniz! İş ilanlarına göz atabilir veya ürünlerimizi keşfedebilirsiniz.\n\nSaygılarımızla,\nKuaför Kariyer Ekibi'
    from_email = settings.EMAIL_HOST_USER if settings.EMAIL_HOST_USER else 'noreply@kuaforplatform.com'
    recipient_list = [user_email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

def send_order_confirmation_email(user_email, order_id, total_amount):
    subject = f'Sipariş Onayı - Sipariş #{order_id}'
    message = f'Merhaba,\n\nSiparişiniz başarıyla alındı. Sipariş numaranız: #{order_id}. Toplam tutar: ₺{total_amount}.\n\nSaygılarımızla,\nKuaför Kariyer Ekibi'
    from_email = settings.EMAIL_HOST_USER if settings.EMAIL_HOST_USER else 'noreply@kuaforplatform.com'
    recipient_list = [user_email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

def award_referral_bonus(referrer_user):
    # Referans verene 100 sadakat puanı bonus ver
    referrer_user.loyalty_points += 100
    referrer_user.save()
    # Bildirim oluştur
    Notification.objects.create(
        user=referrer_user,
        message=f'Tebrikler! Yeni bir kullanıcı davet ettiniz ve 100 sadakat puanı kazandınız.',
        notification_type='OTHER',
        related_object_id=referrer_user.id
    )
