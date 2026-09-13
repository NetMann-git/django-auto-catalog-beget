from django.db import migrations


TEAM = (
    {
        "name": "ИВАН",
        "position": "Главный менеджер",
        "legacy_image": "home/images/2025/09/01/ivan.webp",
        "sort_order": 10,
    },
    {
        "name": "ДАНИЛ",
        "position": "Главный менеджер",
        "legacy_image": "home/images/2025/09/01/danil_aksyuk.webp",
        "sort_order": 20,
    },
)


def seed_team(apps, schema_editor):
    TeamMember = apps.get_model("home", "TeamMember")
    for row in TEAM:
        TeamMember.objects.get_or_create(
            legacy_image=row["legacy_image"],
            defaults={
                "name": row["name"],
                "position": row["position"],
                "sort_order": row["sort_order"],
                "is_published": True,
            },
        )


def unseed_team(apps, schema_editor):
    TeamMember = apps.get_model("home", "TeamMember")
    TeamMember.objects.filter(legacy_image__in=[row["legacy_image"] for row in TEAM]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0005_teammember"),
    ]

    operations = [
        migrations.RunPython(seed_team, unseed_team),
    ]
