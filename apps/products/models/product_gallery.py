# apps/products/models/product_gallery.py
from django.db import models


class ProductGalleryImage(models.Model):
    """
    Дополнительные фотографии товара.
    """

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="gallery",
    )

    image = models.ImageField(
        upload_to="products/gallery/",
    )

    alt = models.CharField(
        max_length=255,
        blank=True,
    )

    sort_order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.product.title}"