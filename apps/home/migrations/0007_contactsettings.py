from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0006_seed_team"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone_primary", models.CharField(max_length=40, verbose_name="Основной телефон")),
                ("phone_secondary", models.CharField(blank=True, max_length=40, verbose_name="Дополнительный телефон")),
                ("address", models.CharField(max_length=255, verbose_name="Адрес")),
                ("map_url", models.URLField(max_length=700, verbose_name="Ссылка на карту Яндекс")),
                ("telegram_url", models.URLField(blank=True, max_length=500, verbose_name="Telegram")),
                ("vk_url", models.URLField(blank=True, max_length=500, verbose_name="ВКонтакте")),
                ("max_url", models.URLField(blank=True, max_length=500, verbose_name="MAX")),
                ("is_published", models.BooleanField(default=True, verbose_name="Показывать секцию на главной")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменено")),
            ],
            options={
                "verbose_name": "Контакты главной страницы",
                "verbose_name_plural": "Контакты главной страницы",
            },
        ),
    ]
