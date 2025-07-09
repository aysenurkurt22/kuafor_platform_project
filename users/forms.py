from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('email', 'is_employer', 'is_customer')

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password']

class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['preferred_locations', 'preferred_skills', 'preferred_product_categories']
        widgets = {
            'preferred_locations': forms.Textarea(attrs={'rows': 2}),
            'preferred_skills': forms.Textarea(attrs={'rows': 2}),
            'preferred_product_categories': forms.Textarea(attrs={'rows': 2}),
        }