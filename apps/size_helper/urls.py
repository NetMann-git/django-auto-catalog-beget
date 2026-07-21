# apps/size_helper/urls.py

from django.urls import path
from . import views

app_name = 'size_helper'

urlpatterns = [
    path('', views.size_helper_form, name='form'),
    path('recommend/', views.get_size_recommendation, name='recommend'),
    path('table/', views.size_table_modal, name='table_modal'),
    path('helper/', views.size_helper_modal, name='helper_modal'),
]