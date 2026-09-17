from django.db import migrations


VIDEO_ONLY_CLIENTS = [
    {
        "name": "Оксана",
        "vehicle": "Changan UNI-T",
        "rutube_url": "https://rutube.ru/play/embed/f44e2211a5634fc5d83109157463b3c2/",
        "sort_order": 520,
    },
    {
        "name": "Юрий",
        "vehicle": "KIA CARNIVAL",
        "rutube_url": "https://rutube.ru/play/embed/811fe0e74ffbbbda136ee5b53f91330d/",
        "sort_order": 530,
    },
    {
        "name": "Сергей",
        "vehicle": "KIA SORENTO",
        "rutube_url": "https://rutube.ru/play/embed/a32419700837ae6c6fbb60473b9c99da/",
        "sort_order": 540,
    },
]


def add_video_only_clients(apps, schema_editor):
    ClientShowcase = apps.get_model("home", "ClientShowcase")

    for item in VIDEO_ONLY_CLIENTS:
        # URL видео уникально идентифицирует именно этот импортированный отзыв.
        if ClientShowcase.objects.filter(rutube_url=item["rutube_url"]).exists():
            continue

        existing = ClientShowcase.objects.filter(
            name=item["name"],
            vehicle=item["vehicle"],
        ).order_by("id").first()

        if existing:
            if not existing.rutube_url:
                existing.rutube_url = item["rutube_url"]
                existing.save(update_fields=("rutube_url",))
            continue

        ClientShowcase.objects.create(
            name=item["name"],
            vehicle=item["vehicle"],
            rutube_url=item["rutube_url"],
            sort_order=item["sort_order"],
            is_published=True,
        )


def remove_video_only_clients(apps, schema_editor):
    ClientShowcase = apps.get_model("home", "ClientShowcase")

    for item in VIDEO_ONLY_CLIENTS:
        ClientShowcase.objects.filter(
            name=item["name"],
            vehicle=item["vehicle"],
            rutube_url=item["rutube_url"],
            image="",
            legacy_image="",
        ).delete()


class Migration(migrations.Migration):
    dependencies = [("home", "0003_clientshowcase_rutube_url")]

    operations = [
        migrations.RunPython(add_video_only_clients, remove_video_only_clients),
    ]
