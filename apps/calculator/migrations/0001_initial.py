# Generated for Django 5.2 on 2026-09-20

import decimal

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    """Создаёт универсальный реестр калькуляторов и ставки утильсбора."""

    initial = True

    dependencies: list[tuple[str, str]] = []

    operations = [
        migrations.CreateModel(
            name="CalculatorDefinition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        max_length=80,
                        unique=True,
                        verbose_name="Системное имя",
                    ),
                ),
                ("title", models.CharField(max_length=160, verbose_name="Название")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Калькулятор",
                "verbose_name_plural": "Калькуляторы",
                "ordering": ("sort_order", "title"),
            },
        ),
        migrations.CreateModel(
            name="RateVersion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=180, verbose_name="Название версии")),
                ("effective_from", models.DateField(verbose_name="Действует с")),
                (
                    "effective_to",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="Действует по",
                    ),
                ),
                (
                    "base_rate",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=14,
                        verbose_name="Базовая ставка, ₽",
                    ),
                ),
                (
                    "source_name",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Нормативный документ",
                    ),
                ),
                ("source_url", models.URLField(blank=True, verbose_name="Ссылка на источник")),
                ("notes", models.TextField(blank=True, verbose_name="Примечание")),
                ("is_active", models.BooleanField(default=True, verbose_name="Опубликована")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "calculator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="rate_versions",
                        to="calculator.calculatordefinition",
                        verbose_name="Калькулятор",
                    ),
                ),
            ],
            options={
                "verbose_name": "Версия ставок",
                "verbose_name_plural": "Версии ставок",
                "ordering": ("-effective_from", "-id"),
            },
        ),
        migrations.CreateModel(
            name="UtilizationRate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "powertrain",
                    models.CharField(
                        choices=[
                            ("combustion", "ДВС или непоследовательный гибрид"),
                            ("electric", "Электромобиль или последовательный гибрид"),
                        ],
                        max_length=20,
                        verbose_name="Тип силовой установки",
                    ),
                ),
                (
                    "usage_mode",
                    models.CharField(
                        choices=[
                            ("personal", "Личное пользование"),
                            ("standard", "Общий коэффициент"),
                        ],
                        default="standard",
                        max_length=20,
                        verbose_name="Режим применения",
                    ),
                ),
                (
                    "age_group",
                    models.CharField(
                        choices=[("new", "Не более 3 лет"), ("used", "Более 3 лет")],
                        max_length=10,
                        verbose_name="Возраст автомобиля",
                    ),
                ),
                (
                    "engine_capacity_min",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Объём двигателя от, см³",
                    ),
                ),
                (
                    "engine_capacity_max",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Объём двигателя до, см³",
                    ),
                ),
                (
                    "power_kw_min",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        verbose_name="Мощность от, кВт",
                    ),
                ),
                (
                    "power_kw_max",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
                        null=True,
                        verbose_name="Мощность до, кВт",
                    ),
                ),
                (
                    "coefficient",
                    models.DecimalField(
                        decimal_places=4,
                        max_digits=12,
                        verbose_name="Коэффициент",
                    ),
                ),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("notes", models.CharField(blank=True, max_length=255, verbose_name="Примечание")),
                (
                    "rate_version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="utilization_rates",
                        to="calculator.rateversion",
                        verbose_name="Версия ставок",
                    ),
                ),
            ],
            options={
                "verbose_name": "Коэффициент утильсбора",
                "verbose_name_plural": "Коэффициенты утильсбора",
                "ordering": (
                    "rate_version",
                    "powertrain",
                    "usage_mode",
                    "engine_capacity_min",
                    "power_kw_min",
                    "age_group",
                ),
            },
        ),
        migrations.AddConstraint(
            model_name="rateversion",
            constraint=models.UniqueConstraint(
                fields=("calculator", "effective_from"),
                name="calculator_unique_rate_version_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="rateversion",
            constraint=models.CheckConstraint(
                condition=Q(effective_to__isnull=True)
                | Q(effective_to__gte=models.F("effective_from")),
                name="calculator_rate_version_valid_period",
            ),
        ),
        migrations.AddConstraint(
            model_name="rateversion",
            constraint=models.CheckConstraint(
                condition=Q(base_rate__gte=0),
                name="calculator_rate_version_nonnegative_base",
            ),
        ),
        migrations.AddIndex(
            model_name="utilizationrate",
            index=models.Index(
                fields=("rate_version", "powertrain", "usage_mode", "age_group"),
                name="calc_util_rate_lookup_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="utilizationrate",
            constraint=models.CheckConstraint(
                condition=Q(coefficient__gte=0),
                name="calculator_util_rate_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="utilizationrate",
            constraint=models.CheckConstraint(
                condition=Q(engine_capacity_min__isnull=True)
                | Q(engine_capacity_max__isnull=True)
                | Q(engine_capacity_max__gte=models.F("engine_capacity_min")),
                name="calculator_util_rate_valid_capacity",
            ),
        ),
        migrations.AddConstraint(
            model_name="utilizationrate",
            constraint=models.CheckConstraint(
                condition=Q(power_kw_min__isnull=True)
                | Q(power_kw_max__isnull=True)
                | Q(power_kw_max__gte=models.F("power_kw_min")),
                name="calculator_util_rate_valid_power",
            ),
        ),
    ]
