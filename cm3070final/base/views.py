from django.shortcuts import render

def home_view(request):
    return render(request, 'base/home.html')

def dashboard_view(request):
    return render(request, 'base/dashboard.html')