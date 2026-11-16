from django.urls import path

from . import views

app_name = "feedback"

urlpatterns = [
    path("", views.usability_study_view, name="study"),
]
