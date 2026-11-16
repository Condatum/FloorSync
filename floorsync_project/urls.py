"""
URL configuration for floorsync_project project.

Feature apps are mounted under their own prefix and namespace (vertical slicing).
`root` and `logout` stay as flat, cross-cutting routes since they are shared by
every feature rather than owned by a single one.
"""
from django.contrib import admin
from django.urls import include, path

from apps.home.views import root_view
from apps.login.views import logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', root_view, name='root'),
    path('logout/', logout_view, name='logout'),
    path('login/', include('apps.login.urls')),
    path('register/', include('apps.register.urls')),
    path('profile/', include('apps.profile.urls')),
    path('settings/', include('apps.user_settings.urls')),
    path('staff/', include('apps.staff.urls')),
    path('floor/', include('apps.venue.urls')),
    path('reservations/', include('apps.reservations.urls')),
    path('feedback/', include('apps.feedback.urls')),
    path('', include('apps.home.urls')),
]
