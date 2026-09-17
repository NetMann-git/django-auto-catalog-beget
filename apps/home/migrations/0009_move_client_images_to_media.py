from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import migrations


STATIC_PREFIX = "home/images/2026/05/04/"
MEDIA_PREFIX = "home/clients/legacy/"


def move_client_images_to_media(apps, schema_editor):
    """
    Копирует legacy-фотографии клиентов из apps/home/static в MEDIA_ROOT
    и переключает ClientShowcase.image на новый media-файл.

    Старый image намеренно пока не очищается: это безопасный fallback
    на время первого деплоя и проверки переноса.
    """
    ClientShowcase = apps.get_model("home", "ClientShowcase")
    static_root = Path(settings.BASE_DIR) / "apps" / "home" / "static"

    queryset = ClientShowcase.objects.filter(
        image="",
        image__startswith=STATIC_PREFIX,
    )

    for client in queryset.iterator():
        source = static_root / client.image
        if not source.is_file():
            # Не ломаем migrate, если конкретный старый файл уже отсутствует.
            continue

        target_name = f"{MEDIA_PREFIX}{source.name}"
        storage = client._meta.get_field("image").storage

        if not storage.exists(target_name):
            storage.save(target_name, ContentFile(source.read_bytes()))

        client.image = target_name
        client.save(update_fields=["image"])


def restore_legacy_usage(apps, schema_editor):
    """
    При откате миграции очищает только ссылки image, созданные этим переносом.
    Сами media-файлы не удаляются, чтобы rollback не уничтожал файлы.
    """
    ClientShowcase = apps.get_model("home", "ClientShowcase")
    ClientShowcase.objects.filter(
        image__startswith=MEDIA_PREFIX,
        image__startswith=STATIC_PREFIX,
    ).update(image="")


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0008_seed_contacts"),
    ]

    operations = [
        migrations.RunPython(move_client_images_to_media, restore_legacy_usage),
    ]
