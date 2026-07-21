# Модель бейджей товара.
from django.db import models
from django.utils.text import slugify

class Badge(models.Model):
    title = models.CharField(
        max_length=50,
        verbose_name="Название"
    )

    slug = models.SlugField(
        max_length=50,
        blank=True,
        unique=True,
        verbose_name="Код"
    )

    class Meta:
        verbose_name = "Бейдж"
        verbose_name_plural = "Бейджи"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title