from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('products', '0007_vehicle_import_source')]
    operations = [
        migrations.AddField(
            model_name=model, name='image_sha256',
            field=models.CharField(max_length=64, blank=True, default='', editable=False),
        ) for model in ('product', 'productgalleryimage')
    ]
