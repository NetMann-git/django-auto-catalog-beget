# apps/search/urls.py

from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search, name='search'),  # если есть страница поиска
    path('suggest/', views.suggest, name='suggest'),
    path('popular/', views.popular, name='popular'),
]