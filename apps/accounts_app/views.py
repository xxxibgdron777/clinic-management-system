from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def profile_view(request):
    return render(request, 'accounts_app/profile.html', {'title': '个人中心'})
