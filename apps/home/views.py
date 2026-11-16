from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.staff.models import StaffAccount
from apps.staff.utils import (
    get_active_concierge,
    get_or_create_staff_account,
    is_approved_staff,
    is_super_admin,
)
from apps.venue.models import Table, Venue


def root_view(request):
    """Redirect root path to home if logged in, or login if anonymous."""
    if request.user.is_authenticated:
        return redirect('home:home')
    return redirect('login:login')


@login_required(login_url='login:login')
def home_view(request):
    """Protected home screen accessible only to authenticated staff."""
    profile = getattr(request.user, 'profile', None)
    staff_account = get_or_create_staff_account(request.user)
    primary_venue = Venue.objects.filter(is_active=True).first()
    active_shift, _ = get_active_concierge(primary_venue)

    visible_tables = Table.objects.filter(is_visible=True)
    available_count = visible_tables.filter(status='AVAILABLE').count()
    reserved_count = visible_tables.filter(status='RESERVED').count()
    occupied_count = visible_tables.filter(status='OCCUPIED').count()
    pending_staff_count = StaffAccount.objects.filter(verification_status='PENDING').count()

    return render(request, 'home/home.html', {
        'user': request.user,
        'profile': profile,
        'staff_account': staff_account,
        'is_approved_staff': is_approved_staff(request.user),
        'is_super_admin': is_super_admin(request.user),
        'available_count': available_count,
        'reserved_count': reserved_count,
        'occupied_count': occupied_count,
        'pending_staff_count': pending_staff_count,
        'active_shift': active_shift,
    })
