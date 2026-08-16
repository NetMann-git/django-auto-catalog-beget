# apps\recommendations\urls.py

from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('manage/', views.manage_recommendations, name='manage'),
    path('add/', views.add_recommendation, name='add'),
    path('edit/<int:pk>/', views.edit_recommendation, name='edit'),
    path('delete/<int:pk>/', views.delete_recommendation, name='delete'),
    path('toggle/<int:pk>/', views.toggle_active, name='toggle_active'),
]