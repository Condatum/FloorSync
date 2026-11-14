from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def root_view(request):
    """Redirect root path to home if logged in, or login if anonymous."""
    if request.user.is_authenticated:
        return redirect('home:home')
    return redirect('login:login')


@login_required(login_url='login:login')
def home_view(request):
    """Protected home screen accessible only to authenticated staff."""
    profile = getattr(request.user, 'profile', None)
    return render(request, 'home/home.html', {
        'user': request.user,
        'profile': profile,
    })
