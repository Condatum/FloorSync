from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import StaffLoginForm


def login_view(request):
    """Staff login view using Django's built-in authentication."""
    if request.user.is_authenticated:
        return redirect('home:home')

    next_url = request.GET.get('next') or request.POST.get('next') or reverse('home:home')

    if request.method == 'POST':
        form = StaffLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}! Signed in to FloorSync.")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = StaffLoginForm(request)

    return render(request, 'login/login.html', {
        'form': form,
        'next': next_url,
    })


def logout_view(request):
    """Logs out the user and redirects back to the login screen."""
    if request.user.is_authenticated:
        auth_logout(request)
        messages.info(request, "You have been logged out of FloorSync.")
    return redirect('login:login')
