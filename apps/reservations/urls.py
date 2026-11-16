from django.urls import path

from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.reservation_list_view, name="list"),
    path("audit/", views.audit_log_view, name="audit"),
]
