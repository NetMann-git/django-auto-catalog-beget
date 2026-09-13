from django.db import models


class ClientShowcase(models.Model):
    """Карточка клиента для секции «Наши клиенты» на главной странице."""

    name = models.CharField(max_length=120, verbose_name="Имя клиента")
    vehicle = models.CharField(max_length=180, verbose_name="Автомобиль")
    image = models.ImageField(
        upload_to="home/clients/%Y/%m/",
        blank=True,
        verbose_name="Фотография",
    )
    legacy_image = models.CharField(
        max_length=255,
        blank=True,
        editable=False,
        verbose_name="Старое статическое изображение",
    )
    sort_order = models.PositiveIntegerField(
        default=100,
        db_index=True,
        verbose_name="Порядок вывода",
        help_text="Чем меньше число, тем раньше карточка показывается.",
    )
    is_published = models.BooleanField(default=True, db_index=True, verbose_name="Опубликован")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Изменён")

    class Meta:
        ordering = ("sort_order", "id")
        verbose_name = "Клиент на главной"
        verbose_name_plural = "Клиенты на главной"

    def __str__(self):
        return f"{self.name} — {self.vehicle}"

    @property
    def has_image(self):
        return bool(self.image or self.legacy_image)
