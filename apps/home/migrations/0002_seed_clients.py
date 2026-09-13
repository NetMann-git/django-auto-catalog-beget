from django.db import migrations


def seed_clients(apps, schema_editor):
    ClientShowcase = apps.get_model("home", "ClientShowcase")
    rows = [
        ('Луиза', 'Audi Q3', 'home/images/2026/05/04/luiza.webp', 10),
        ('Наталья', 'Mazda CX-5', 'home/images/2026/05/04/natalash5.webp', 20),
        ('Денис', 'KIA K5', 'home/images/2026/05/04/denisk5.webp', 30),
        ('Виталий', 'KIA Sorento', 'home/images/2026/05/04/vitalij.webp', 40),
        ('Наталья', 'Hyundai Kona', 'home/images/2026/05/04/natala.webp', 50),
        ('Александр', 'KIA K5', 'home/images/2026/05/04/aleksandrk5.webp', 60),
        ('Юлия', 'KIA Niro', 'home/images/2026/05/04/ulia.webp', 70),
        ('Руслан', 'KIA Seltos', 'home/images/2026/05/04/ruslan.webp', 80),
        ('Борис', 'Volkswagen Lamando', 'home/images/2026/05/04/boris.webp', 90),
        ('Андрей', 'Jeep Compass', 'home/images/2026/05/04/andrejkompass.webp', 100),
        ('Ольга', 'Mercedes GLB 220d', 'home/images/2026/05/04/olgaglb.webp', 110),
        ('Олег', 'Zeekr X', 'home/images/2026/05/04/olegzikr.webp', 120),
        ('Роман', 'Porsche 911 Carrera', 'home/images/2026/05/04/roma911.webp', 130),
        ('Здрава', 'Mercedes A220d', 'home/images/2026/05/04/zdrava.webp', 140),
        ('Евгений', 'Hyundai Palisade', 'home/images/2026/05/04/evgenijpalis.webp', 150),
        ('Игорь', 'Renault Samsung XM3', 'home/images/2026/05/04/igorhm3.webp', 160),
        ('Сергей', 'BMW X5', 'home/images/2026/05/04/sergejiks.webp', 170),
        ('Марина', 'Volkswagen Tiguan', 'home/images/2026/05/04/marinka.webp', 180),
        ('Александр', 'KIA Sportage', 'home/images/2026/05/04/aleksandr1.webp', 190),
        ('Петр', 'KIA Carnival', 'home/images/2026/05/04/petr.webp', 200),
        ('Иван', 'BMW 630i GT', 'home/images/2026/05/04/ivan.webp', 210),
        ('Анна', 'KIA Carnival', 'home/images/2026/05/04/anna.webp', 220),
        ('Роман', 'BMW X5', 'home/images/2026/05/04/roma.webp', 230),
        ('Николай', 'Peugeot 3008', 'home/images/2026/05/04/nikolaj.webp', 240),
        ('Герман', 'Hyundai Avante', 'home/images/2026/05/04/german.webp', 250),
        ('Олеся', 'BMW X4', 'home/images/2026/05/04/olesah4.webp', 260),
        ('Сергей и Алена', 'Hyundai TUCSON 4WD', 'home/images/2026/05/04/sergej-i-alena.webp', 270),
        ('Максим', 'Hyundai SONATA Premium Family', 'home/images/2026/05/04/maksim.webp', 280),
        ('Сергей', 'SsangYong TORRES', 'home/images/2026/05/04/sergej.webp', 290),
        ('Олег', 'BMW X4', 'home/images/2026/05/04/oleg.webp', 300),
        ('Дмитрий', 'SsangYong REXTON G4', 'home/images/2026/05/04/dimka.webp', 310),
        ('Станислав', 'Renault SAMSUNG XM3', 'home/images/2026/05/04/stanislav.webp', 320),
        ('Ольга', 'KIA Morning', 'home/images/2026/05/04/zensina.webp', 330),
        ('Денис', 'Mercedes C-clssse (W206)', 'home/images/2026/05/04/denis.webp', 340),
        ('Олеся', 'Changan UNI-T', 'home/images/2026/05/04/olesa.webp', 350),
        ('Игорь', 'Genesis GV80', 'home/images/2026/05/04/igor.webp', 360),
        ('Анатолий', 'Renault SAMSUNG XM3', 'home/images/2026/05/04/tolik.webp', 370),
        ('Арсен', 'Hyundai PALISADE', 'home/images/2026/05/04/arsen.webp', 380),
        ('Олеся', 'BMW X5', 'home/images/2026/05/04/OlesaH.webp', 390),
        ('Дмитрий и Людмила', 'Hyundai TUCSON', 'home/images/2026/05/04/dmitrij.webp', 400),
        ('Александр', 'KIA K3', 'home/images/2026/05/04/aleksandr.webp', 410),
        ('Муледин', 'KIA K3', 'home/images/2026/05/04/muledin.webp', 420),
        ('Вячеслав', 'Renault SAMSUNG XM3', 'home/images/2026/05/04/vaceslav.webp', 430),
        ('Пётр', 'Hyundai TUCSON', 'home/images/2026/05/04/peta.webp', 440),
        ('Егор', 'Renault SAMSUNG XM3', 'home/images/2026/05/04/6.Muzik-2.webp', 450),
        ('Дмитрий', 'KIA SORENTO', 'home/images/2026/05/04/7.Dmitrij-2.webp', 460),
        ('Ольга', 'KIA K3', 'home/images/2026/05/04/5.Devocka-2.webp', 470),
        ('Алексей', 'GENESIS GV70', 'home/images/2026/05/04/4.Lesa-2.webp', 480),
        ('Любовь', 'MINI COOPER', 'home/images/2026/05/04/3.Luba-2.webp', 490),
        ('Дмитрий', 'KIA SORENTO', 'home/images/2026/05/04/2.Dimon-2.webp', 500),
        ('София', 'KIA NIRO', 'home/images/2026/05/04/1.Sona-2.webp', 510),
    ]
    ClientShowcase.objects.bulk_create(
        [
            ClientShowcase(
                name=name,
                vehicle=vehicle,
                legacy_image=legacy_image,
                sort_order=sort_order,
                is_published=True,
            )
            for name, vehicle, legacy_image, sort_order in rows
        ]
    )


def unseed_clients(apps, schema_editor):
    ClientShowcase = apps.get_model("home", "ClientShowcase")
    ClientShowcase.objects.filter(legacy_image__startswith="home/images/2026/05/04/").delete()


class Migration(migrations.Migration):
    dependencies = [("home", "0001_initial")]

    operations = [migrations.RunPython(seed_clients, unseed_clients)]
