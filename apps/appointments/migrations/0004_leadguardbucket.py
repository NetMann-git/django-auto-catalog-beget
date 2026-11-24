"""Create shared anti-spam state and its transaction mutex."""
from django.db import migrations, models
from django.utils import timezone


def seed_lock(apps, schema_editor):
    bucket = apps.get_model('appointments', 'LeadGuardBucket')
    bucket.objects.using(schema_editor.connection.alias).get_or_create(
        key='lock', defaults={'started_at': timezone.now(), 'count': 0},
    )


class Migration(migrations.Migration):
    dependencies = [
        ('appointments', '0003_callbackrequest_city_callbackrequest_comment_and_more'),
    ]
    operations = [
        migrations.CreateModel(
            name='LeadGuardBucket',
            fields=[
                ('key', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('started_at', models.DateTimeField()),
                ('count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Счётчик защиты заявок',
                'verbose_name_plural': 'Счётчики защиты заявок',
            },
        ),
        migrations.RunPython(seed_lock, migrations.RunPython.noop),
    ]
