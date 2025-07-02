from django.shortcuts import render

def about_us(request):
    return render(request, 'pages/about_us.html')

def terms_of_service(request):
    return render(request, 'pages/terms_of_service.html')

def privacy_policy(request):
    return render(request, 'pages/privacy_policy.html')
