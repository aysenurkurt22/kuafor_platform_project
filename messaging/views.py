from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Message
from users.models import CustomUser
from notifications.models import Notification # Notification modelini import et

@login_required
def inbox(request):
    # Kullanıcının gönderdiği veya aldığı tüm mesajları al
    messages = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).order_by('-timestamp')

    # Konuşmaları grupla
    conversations = {}
    for message in messages:
        if message.sender == request.user:
            other_user = message.receiver
        else:
            other_user = message.sender
        
        if other_user.id not in conversations:
            conversations[other_user.id] = {
                'user': other_user,
                'last_message': message,
                'unread_count': 0
            }
        if message.receiver == request.user and not message.is_read:
            conversations[other_user.id]['unread_count'] += 1

    # Konuşmaları son mesaja göre sırala
    sorted_conversations = sorted(conversations.values(), key=lambda x: x['last_message'].timestamp, reverse=True)

    return render(request, 'messaging/inbox.html', {'conversations': sorted_conversations})

@login_required
def conversation(request, user_id):
    other_user = get_object_or_404(CustomUser, pk=user_id)
    
    # Kullanıcılar arasındaki mesajları al
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=other_user)) |
        (Q(sender=other_user) & Q(receiver=request.user))
    ).order_by('timestamp')

    # Okunmamış mesajları okunmuş olarak işaretle
    messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=request.user, receiver=other_user, content=content)
            # Bildirim oluştur
            Notification.objects.create(
                user=other_user,
                message=f'{request.user.username} size yeni bir mesaj gönderdi.',
                notification_type='MESSAGE',
                related_object_id=request.user.id # Mesajı gönderen kullanıcının ID'si
            )
            return redirect('conversation', user_id=user_id)

    return render(request, 'messaging/conversation.html', {'other_user': other_user, 'messages': messages})
