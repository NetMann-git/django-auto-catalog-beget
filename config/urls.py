# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.home.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('smart_selects/', include('smart_selects.urls')),  # ДОБАВИТЬ ЭТУ СТРОКУ
    path('', home, name='home'),
    path('catalog/', include('apps.products.urls')),
    path('wishlist/', include('apps.wishlist.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('appointments/', include('apps.appointments.urls')),
    path('size-helper/', include('apps.size_helper.urls')),
    path('account/', include('apps.users.urls')),
    path('search/', include('apps.search.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
