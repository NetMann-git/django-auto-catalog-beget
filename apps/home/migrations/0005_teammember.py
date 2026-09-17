from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0004_add_video_only_clients"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamMember",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="Имя")),
                ("position", models.CharField(max_length=180, verbose_name="Должность")),
                ("image", models.ImageField(blank=True, upload_to="home/team/%Y/%m/", verbose_name="Фотография")),
                ("image", models.CharField(blank=True, editable=False, max_length=255, verbose_name="Старое статическое изображение")),
                ("sort_order", models.PositiveIntegerField(db_index=True, default=100, help_text="Чем меньше число, тем раньше сотрудник показывается.", verbose_name="Порядок вывода")),
                ("is_published", models.BooleanField(db_index=True, default=True, verbose_name="Опубликован")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменён")),
            ],
            options={
                "verbose_name": "Сотрудник команды",
                "verbose_name_plural": "Команда",
                "ordering": ("sort_order", "id"),
            },
        ),
    ]
