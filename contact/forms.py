from django import forms
from .models import Report, ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'details']
        widgets = {
            'details': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Lütfen şikayetinizle ilgili ek detaylar verin.'}),
        }