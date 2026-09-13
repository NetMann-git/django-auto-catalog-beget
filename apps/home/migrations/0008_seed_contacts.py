from django.db import migrations


def seed_contacts(apps, schema_editor):
    ContactSettings = apps.get_model("home", "ContactSettings")
    ContactSettings.objects.update_or_create(
        pk=1,
        defaults={
            "phone_primary": "+7(988)580-88-99",
            "phone_secondary": "+7(928)959-54-59",
            "address": "Ростов-на-Дону, Максима Горького 249",
            "map_url": "https://yandex.ru/map-widget/v1/?z=12&ol=biz&oid=11795644110",
            "telegram_url": "https://t.me/auto_korea_pod_zakaz",
            "vk_url": "https://vk.com/podberemauto",
            "max_url": "https://xn----8sbbggha0dnibq5a.xn--p1ai/max.ru/channel_podberem_auto",
            "is_published": True,
        },
    )


def remove_seeded_contacts(apps, schema_editor):
    ContactSettings = apps.get_model("home", "ContactSettings")
    ContactSettings.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0007_contactsettings"),
    ]

    operations = [
        migrations.RunPython(seed_contacts, remove_seeded_contacts),
    ]
