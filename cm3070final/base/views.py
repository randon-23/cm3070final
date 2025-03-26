from django.shortcuts import render

def custom_404(request, exception):
    template = 'base/base_error_authenticated.html' if request.user.is_authenticated else 'base/base_error.html'
    return render(request, template, {'status_code': 404}, status=404)

def custom_403(request, exception):
    template = 'base/base_error_authenticated.html' if request.user.is_authenticated else 'base/base_error.html'
    return render(request, template, {'status_code': 403}, status=403)

def custom_500(request):
    template = 'base/base_error_authenticated.html'  # 500 doesn’t receive request.user
    return render(request, template, {'status_code': 500}, status=500)

def custom_400(request, exception):
    template = 'base/base_error_authenticated.html' if request.user.is_authenticated else 'base/base_error.html'
    return render(request, template, {'status_code': 400}, status=400)