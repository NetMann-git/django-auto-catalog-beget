from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CallbackRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, verbose_name='Имя')),
                ('phone', models.CharField(max_length=30, verbose_name='Телефон')),
                ('status', models.CharField(choices=[('new', 'Новая'), ('processed', 'Обработана'), ('cancelled', 'Отменена')], db_index=True, default='new', max_length=20, verbose_name='Статус')),
                ('source', models.CharField(default='homepage', max_length=100, verbose_name='Источник')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Создана')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Изменена')),
            ],
            options={
                'verbose_name': 'Заявка на обратный звонок',
                'verbose_name_plural': 'Заявки на обратный звонок',
                'ordering': ['-created_at'],
            },
        ),
    ]
