from django.core.mail import send_mail
from django.conf import settings

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

