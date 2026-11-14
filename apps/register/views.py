from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import StaffRegistrationForm


def register_view(request):
    """Staff registration view. Creates user and redirects to login on success."""
    if request.user.is_authenticated:
        return redirect('home:home')

    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Account for '{user.username}' created successfully! Please log in with your credentials."
            )
            return redirect('login:login')
        else:
            messages.error(request, "Registration failed. Please fix the indicated errors below.")
    else:
        form = StaffRegistrationForm()

    return render(request, 'register/register.html', {'form': form})
