# apps/appointments/models.py

from django.db import models
from django.conf import settings
from apps.products.models import Product
from django.core.exceptions import ValidationError



class Appointment(models.Model):
    """
    Запись на примерку.
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('new', 'Новая'),
        ('confirmed', 'Подтверждена'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        verbose_name='Товар',
    )

    name = models.CharField(
        max_length=100,
        verbose_name='Имя',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        verbose_name='Пользователь',
    )

    phone = models.CharField(
        max_length=20,
        verbose_name='Телефон',
    )

    email = models.EmailField(
        blank=True,
        verbose_name='Email',
    )

    date = models.DateField(
        verbose_name='Дата примерки',
    )

    time = models.TimeField(
        verbose_name='Время примерки',
    )

    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def clean(self):
        # Проверяем, не занят ли слот (только для новых и подтверждённых записей)
        if self.status in ['pending', 'confirmed']:
            existing = Appointment.objects.filter(
                date=self.date,
                time=self.time,
                status__in=['pending', 'confirmed']
            ).exclude(id=self.id)
            if existing.exists():
                raise ValidationError(f'Это время {self.time} на {self.date} уже занято другой записью.')

    def save(self, *args, **kwargs):
        self.full_clean()  # вызывает clean() перед сохранением
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Запись на примерку'
        verbose_name_plural = 'Записи на примерку'

    def __str__(self):
        return f'{self.name} — {self.date} {self.time}'


class WorkingHours(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]

    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, unique=True, verbose_name='День недели')
    start_time = models.TimeField(verbose_name='Начало работы')
    end_time = models.TimeField(verbose_name='Конец работы')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        ordering = ['day_of_week']
        verbose_name = 'Рабочее время'
        verbose_name_plural = 'Рабочее время'

    def __str__(self):
        return f'{self.get_day_of_week_display()}: {self.start_time} - {self.end_time}'