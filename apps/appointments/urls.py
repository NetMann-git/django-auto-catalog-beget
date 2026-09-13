# apps/appointments/urls.py

from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('form/', views.appointment_form, name='form'),
    path('form/<int:product_id>/', views.appointment_form, name='form_for_product'),
    path('submit/', views.appointment_submit, name='submit'),
    path('callback-submit/', views.callback_submit, name='callback_submit'),
    path('slots/<str:date>/', views.get_available_slots, name='slots'),
]