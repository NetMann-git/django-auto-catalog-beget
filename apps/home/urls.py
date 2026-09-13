from django.urls import path

from . import manage_views

app_name = "home"

urlpatterns = [
    path("clients/", manage_views.client_list_manage, name="client_list_manage"),
    path("clients/create/", manage_views.client_create, name="client_create"),
    path("clients/<int:client_id>/edit/", manage_views.client_edit, name="client_edit"),
    path("clients/<int:client_id>/toggle-published/", manage_views.client_toggle_published, name="client_toggle_published"),
]
