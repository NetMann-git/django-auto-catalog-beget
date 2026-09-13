from django.db import migrations, models


VIDEO_REVIEWS = [
    ("Станислав", "Renault SAMSUNG XM3", ["https://rutube.ru/play/embed/b01059d843b5c69740fb2ae3d1cd682d/"]),
    ("Олеся", "BMW X5", ["https://rutube.ru/play/embed/4217e2a2d92bf8fa77e850b174dc72ab/"]),
    ("Дмитрий и Людмила", "Hyundai TUCSON", ["https://rutube.ru/play/embed/4a86d06a11c8893d6c55a2bf02f7d75d/"]),
    ("Анатолий", "Renault SAMSUNG XM3", ["https://rutube.ru/play/embed/f8f70a591e420fd1c7402d1641dbb6db/"]),
    ("Муледин", "KIA K3", ["https://rutube.ru/play/embed/5ae31ff7e66ca83e9cc30187e0bae5f7/"]),
    ("Вячеслав", "Renault SAMSUNG XM3", ["https://rutube.ru/play/embed/db1b14b8363b7a7c37b8ee23ad7984e4/"]),
    ("Александр", "KIA K3", ["https://rutube.ru/play/embed/9ffe959f409d21fb7d924b942807a7fb/"]),
    ("Пётр", "Hyundai TUCSON", ["https://rutube.ru/play/embed/192bfd8589d12a6f7cf0a266871d5624/"]),
    ("Дмитрий", "KIA SORENTO", [
        "https://rutube.ru/play/embed/ec72ac2c9a13b51bd8ee93484311a739/",
        "https://rutube.ru/play/embed/4040d9673ed47fd30b2f6cfbb0489981/",
    ]),
    ("София", "KIA NIRO", ["https://rutube.ru/play/embed/6136ac43461f181c7de8e51e3baaacd2/"]),
]


def import_video_reviews(apps, schema_editor):
    ClientShowcase = apps.get_model("home", "ClientShowcase")
    for name, vehicle, urls in VIDEO_REVIEWS:
        clients = list(
            ClientShowcase.objects.filter(name=name, vehicle=vehicle, rutube_url="").order_by("id")[:len(urls)]
        )
        for client, url in zip(clients, urls):
            client.rutube_url = url
            client.save(update_fields=("rutube_url",))



def clear_imported_video_reviews(apps, schema_editor):
    ClientShowcase = apps.get_model("home", "ClientShowcase")
    for _, _, urls in VIDEO_REVIEWS:
        for url in urls:
            ClientShowcase.objects.filter(rutube_url=url).update(rutube_url="")


class Migration(migrations.Migration):
    dependencies = [("home", "0002_seed_clients")]

    operations = [
        migrations.AddField(
            model_name="clientshowcase",
            name="rutube_url",
            field=models.URLField(
                blank=True,
                help_text="Оставьте пустым, если клиент не записывал видеоотзыв.",
                max_length=500,
                verbose_name="Ссылка на видеоотзыв Rutube",
            ),
        ),
        migrations.RunPython(import_video_reviews, clear_imported_video_reviews),
    ]
