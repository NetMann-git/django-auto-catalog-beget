# apps\recommendations\urls.py

from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('manage/', views.manage_recommendations, name='manage'),
    path('delete/<int:pk>/', views.delete_recommendation, name='delete'),
]