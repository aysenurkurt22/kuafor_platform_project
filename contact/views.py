from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm

def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Mesajınız başarıyla gönderildi. En kısa sürede size geri döneceğiz.')
            return redirect('contact_us')
    else:
        form = ContactForm()
    return render(request, 'contact/contact_us.html', {'form': form})