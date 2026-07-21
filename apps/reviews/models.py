# apps/reviews/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.products.models import Product


class Review(models.Model):
    """
    Отзыв о товаре.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Товар",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
        verbose_name="Пользователь",
    )

    guest_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Имя гостя",
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка",
    )

    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Заголовок",
    )

    text = models.TextField(verbose_name="Текст отзыва")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    is_published = models.BooleanField(default=False, verbose_name="Опубликован")
    is_verified = models.BooleanField(default=False, verbose_name="Подтверждённая покупка")

    helpful_count = models.PositiveIntegerField(default=0, verbose_name="Полезных")
    unhelpful_count = models.PositiveIntegerField(default=0, verbose_name="Бесполезных")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        name = self.user.username if self.user else self.guest_name or "Гость"
        return f"{name} — {self.product.title} ({self.rating}★)"

    def get_author_name(self):
        """Возвращает имя автора для отображения."""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.guest_name or "Гость"


class ReviewReply(models.Model):
    """
    Ответ администрации на отзыв.
    """
    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,
        related_name="reply",
        verbose_name="Отзыв",
    )

    text = models.TextField(verbose_name="Текст ответа")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата ответа")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Ответ на отзыв"
        verbose_name_plural = "Ответы на отзывы"

    def __str__(self):
        return f"Ответ на отзыв {self.review.id}"

class ReviewImage(models.Model):
    """
    Фотографии в отзыве.
    """

    review = models.ForeignKey(
        "Review",  # ← строковая ссылка, чтобы не было ошибки порядка
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Отзыв",
    )
    image = models.ImageField(upload_to="reviews/", verbose_name="Изображение")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Фото отзыва"
        verbose_name_plural = "Фото отзывов"

    def __str__(self):
        return f"Фото к отзыву {self.review.id}"

class ReviewVote(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="votes",
        verbose_name="Отзыв",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_votes",
        verbose_name="Пользователь",
    )
    session_key = models.CharField(max_length=40, blank=True, null=True, verbose_name="Ключ сессии")
    is_helpful = models.BooleanField(verbose_name="Полезно")

    class Meta:
        unique_together = ("review", "user", "session_key")  # один голос от одного пользователя/сессии
        verbose_name = "Голос за отзыв"
        verbose_name_plural = "Голоса за отзывы"

    def __str__(self):
        return f"{self.review.id} - {'Полезно' if self.is_helpful else 'Бесполезно'}"