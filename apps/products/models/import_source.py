"""Identity and original data of a manually confirmed vehicle import."""
from django.db import models


class VehicleImportSource(models.Model):
    """Listing identity is distinct from Encar's internal vehicle identity."""

    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='import_sources')
    source = models.CharField(max_length=20, default='encar', editable=False)
    listing_id = models.CharField(max_length=30)
    internal_vehicle_id = models.CharField(max_length=30, blank=True)
    source_url = models.URLField(max_length=500)
    imported_at = models.DateTimeField(auto_now=True)
    retrieved_at = models.DateTimeField(null=True, blank=True)
    raw_json = models.JSONField()
    source_price = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    source_currency = models.CharField(max_length=3, blank=True)
    original_description = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('source', 'listing_id'), name='unique_vehicle_source_listing')]
        verbose_name = 'Источник импорта автомобиля'
        verbose_name_plural = 'Источники импорта автомобилей'
