from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0009_move_client_images_to_media"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="clientshowcase",
            name="legacy_image",
        ),
    ]
