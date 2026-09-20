"""URL-маршруты раздела калькуляторов."""

from django.urls import path

from . import views

app_name = "calculator"

urlpatterns = [
    path("util-sbor/", views.utilization_fee, name="utilization_fee"),
    path("rastamozhka/", views.customs_clearance, name="customs_clearance"),
]
