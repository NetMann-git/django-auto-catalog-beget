# Generated manually for Brand admin ordering.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_alter_product_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="brand",
            name="sort_order",
            field=models.PositiveIntegerField(
                db_index=True,
                default=0,
                help_text="Меньшее число выводится раньше.",
                verbose_name="Порядок",
            ),
        ),
    ]
