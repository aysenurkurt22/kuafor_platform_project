from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def notification_list(request):
    # Kullanıcının okunmamış tüm bildirimlerini al ve okundu olarak işaretle
    notifications = request.user.notifications.all()
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})

@login_required
def mark_all_as_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('notifications:notification_list')
