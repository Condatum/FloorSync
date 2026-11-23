from django.urls import path

from . import views

app_name = "venue"

urlpatterns = [
    path("", views.public_map_view, name="public_map"),
    path("api/status/", views.floor_status_api_view, name="status_api"),
    path("hub/", views.admin_hub_view, name="admin_hub"),
    path("manage/", views.spatial_manage_view, name="spatial_manage"),
]
