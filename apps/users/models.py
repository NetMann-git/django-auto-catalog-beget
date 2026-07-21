# apps/users/models.py

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = [
        ('customer', 'Покупатель'),
        ('consultant', 'Консультант'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, verbose_name='О себе')

    # Для консультанта
    is_available = models.BooleanField(default=True, verbose_name='Доступен для записи')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'
