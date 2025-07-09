from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from .forms import ContactForm, ReportForm
from .models import Report, ContactMessage
import re

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            # Basic spam check
            spam_keywords = ['buy now', 'free money', 'casino', 'sex', 'viagra', 'earn money', 'investment', 'urgent']
            is_spam = False
            for keyword in spam_keywords:
                if keyword in message.subject.lower() or keyword in message.message.lower():
                    is_spam = True
                    break
            message.is_spam = is_spam
            message.save()
            if is_spam:
                messages.warning(request, 'Mesajınız spam olarak işaretlenmiş olabilir ve incelenecektir.')
            else:
                messages.success(request, 'Mesajınız başarıyla gönderildi. En kısa sürede size geri döneceğiz.')
            return redirect('contact:contact_us')
    else:
        form = ContactForm()
    return render(request, 'contact/contact_us.html', {'form': form})

@login_required
def report_content(request, content_type_id, object_id):
    content_type = get_object_or_404(ContentType, pk=content_type_id)
    content_object = content_type.get_object_for_this_type(pk=object_id)

    if Report.objects.filter(reporter=request.user, content_type=content_type, object_id=object_id).exists():
        messages.warning(request, 'Bu içeriği zaten şikayet ettiniz.')
        return redirect(content_object.get_absolute_url())

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.content_object = content_object
            report.save()
            messages.success(request, 'Şikayetiniz başarıyla alındı ve incelenmek üzere ekibimize iletildi.')
            return redirect(content_object.get_absolute_url())
    else:
        form = ReportForm()

    context = {
        'form': form,
        'content_object': content_object,
    }
    return render(request, 'contact/report_form.html', context)
