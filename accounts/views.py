from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import StaffRegistrationForm, StaffLoginForm


def root_view(request):
    """Redirect root path to home if logged in, or login if anonymous."""
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')


def login_view(request):
    """Staff login view using Django's built-in authentication."""
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next') or request.POST.get('next') or 'home'

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

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': next_url,
    })


def register_view(request):
    """Staff registration view. Creates user and redirects to login on success."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Account for '{user.username}' created successfully! Please log in with your credentials."
            )
            return redirect('login')
        else:
            messages.error(request, "Registration failed. Please fix the indicated errors below.")
    else:
        form = StaffRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required(login_url='login')
def home_view(request):
    """Protected home screen accessible only to authenticated staff."""
    return render(request, 'accounts/home.html', {
        'user': request.user,
    })


def logout_view(request):
    """Logs out the user and redirects back to the login screen."""
    if request.user.is_authenticated:
        auth_logout(request)
        messages.info(request, "You have been logged out of FloorSync.")
    return redirect('login')
