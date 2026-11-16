from django.urls import path

from . import views

app_name = "staff"

urlpatterns = [
    path("vetting/", views.vetting_view, name="vetting"),
    path("duty/", views.duty_view, name="duty"),
]
