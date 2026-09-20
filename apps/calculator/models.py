"""Модели калькуляторов и версионируемых ставок."""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class CalculatorDefinition(models.Model):
    """Калькулятор, доступный в универсальном разделе сайта."""

    slug = models.SlugField(
        max_length=80,
        unique=True,
        verbose_name="Системное имя",
    )
    title = models.CharField(max_length=160, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "title")
        verbose_name = "Калькулятор"
        verbose_name_plural = "Калькуляторы"

    def __str__(self) -> str:
        return self.title


class RateVersion(models.Model):
    """Версия нормативных ставок с ограниченным периодом действия."""

    calculator = models.ForeignKey(
        CalculatorDefinition,
        on_delete=models.PROTECT,
        related_name="rate_versions",
        verbose_name="Калькулятор",
    )
    name = models.CharField(max_length=180, verbose_name="Название версии")
    effective_from = models.DateField(verbose_name="Действует с")
    effective_to = models.DateField(
        blank=True,
        null=True,
        verbose_name="Действует по",
    )
    base_rate = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Базовая ставка, ₽",
    )
    source_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Нормативный документ",
    )
    source_url = models.URLField(blank=True, verbose_name="Ссылка на источник")
    notes = models.TextField(blank=True, verbose_name="Примечание")
    is_active = models.BooleanField(default=True, verbose_name="Опубликована")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-effective_from", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("calculator", "effective_from"),
                name="calculator_unique_rate_version_start",
            ),
            models.CheckConstraint(
                condition=Q(effective_to__isnull=True)
                | Q(effective_to__gte=models.F("effective_from")),
                name="calculator_rate_version_valid_period",
            ),
            models.CheckConstraint(
                condition=Q(base_rate__gte=0),
                name="calculator_rate_version_nonnegative_base",
            ),
        ]
        verbose_name = "Версия ставок"
        verbose_name_plural = "Версии ставок"

    def __str__(self) -> str:
        return f"{self.calculator}: {self.name}"

    def clean(self) -> None:
        """Запрещает пересекающиеся опубликованные версии ставок."""
        super().clean()

        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError(
                {"effective_to": "Дата окончания не может быть раньше начала."}
            )

        if not self.is_active or not self.calculator_id:
            return

        period_end = self.effective_to or date.max
        overlapping = (
            RateVersion.objects.filter(
                calculator_id=self.calculator_id,
                is_active=True,
                effective_from__lte=period_end,
            )
            .filter(
                Q(effective_to__isnull=True)
                | Q(effective_to__gte=self.effective_from)
            )
            .exclude(pk=self.pk)
        )
        if overlapping.exists():
            raise ValidationError(
                "Период пересекается с другой опубликованной версией ставок."
            )


class UtilizationRate(models.Model):
    """Коэффициент утилизационного сбора для диапазона параметров ТС."""

    class Powertrain(models.TextChoices):
        COMBUSTION = "combustion", "ДВС или непоследовательный гибрид"
        ELECTRIC = "electric", "Электромобиль или последовательный гибрид"

    class UsageMode(models.TextChoices):
        PERSONAL = "personal", "Личное пользование"
        STANDARD = "standard", "Общий коэффициент"

    class AgeGroup(models.TextChoices):
        NEW = "new", "Не более 3 лет"
        USED = "used", "Более 3 лет"

    rate_version = models.ForeignKey(
        RateVersion,
        on_delete=models.CASCADE,
        related_name="utilization_rates",
        verbose_name="Версия ставок",
    )
    powertrain = models.CharField(
        max_length=20,
        choices=Powertrain.choices,
        verbose_name="Тип силовой установки",
    )
    usage_mode = models.CharField(
        max_length=20,
        choices=UsageMode.choices,
        default=UsageMode.STANDARD,
        verbose_name="Режим применения",
    )
    age_group = models.CharField(
        max_length=10,
        choices=AgeGroup.choices,
        verbose_name="Возраст автомобиля",
    )
    engine_capacity_min = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Объём двигателя от, см³",
    )
    engine_capacity_max = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Объём двигателя до, см³",
    )
    power_kw_min = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Мощность от, кВт",
    )
    power_kw_max = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Мощность до, кВт",
    )
    coefficient = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Коэффициент",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    notes = models.CharField(max_length=255, blank=True, verbose_name="Примечание")

    class Meta:
        ordering = (
            "rate_version",
            "powertrain",
            "usage_mode",
            "engine_capacity_min",
            "power_kw_min",
            "age_group",
        )
        indexes = [
            models.Index(
                fields=(
                    "rate_version",
                    "powertrain",
                    "usage_mode",
                    "age_group",
                ),
                name="calc_util_rate_lookup_idx",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(coefficient__gte=0),
                name="calculator_util_rate_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(engine_capacity_min__isnull=True)
                | Q(engine_capacity_max__isnull=True)
                | Q(engine_capacity_max__gte=models.F("engine_capacity_min")),
                name="calculator_util_rate_valid_capacity",
            ),
            models.CheckConstraint(
                condition=Q(power_kw_min__isnull=True)
                | Q(power_kw_max__isnull=True)
                | Q(power_kw_max__gte=models.F("power_kw_min")),
                name="calculator_util_rate_valid_power",
            ),
        ]
        verbose_name = "Коэффициент утильсбора"
        verbose_name_plural = "Коэффициенты утильсбора"

    def __str__(self) -> str:
        return f"{self.rate_version.name}: {self.coefficient}"

    def clean(self) -> None:
        """Проверяет корректность диапазонов коэффициента."""
        super().clean()

        errors: dict[str, str] = {}
        if (
            self.engine_capacity_min is not None
            and self.engine_capacity_max is not None
            and self.engine_capacity_min > self.engine_capacity_max
        ):
            errors["engine_capacity_max"] = (
                "Верхняя граница объёма должна быть не меньше нижней."
            )

        if (
            self.power_kw_min is not None
            and self.power_kw_max is not None
            and self.power_kw_min > self.power_kw_max
        ):
            errors["power_kw_max"] = (
                "Верхняя граница мощности должна быть не меньше нижней."
            )

        if self.powertrain == self.Powertrain.ELECTRIC and (
            self.engine_capacity_min is not None
            or self.engine_capacity_max is not None
        ):
            errors["engine_capacity_min"] = (
                "Для электромобиля диапазон объёма двигателя не заполняется."
            )

        if errors:
            raise ValidationError(errors)


class CurrencyRate(models.Model):
    """Курс иностранной валюты к рублю на определённую дату."""

    code = models.CharField(max_length=3, verbose_name="Код валюты")
    nominal = models.PositiveIntegerField(default=1, verbose_name="Номинал")
    rate_to_rub = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        verbose_name="Курс к рублю",
    )
    effective_date = models.DateField(verbose_name="Дата курса")
    source_url = models.URLField(blank=True, verbose_name="Источник")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-effective_date", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("code", "effective_date"),
                name="calculator_unique_currency_rate_date",
            ),
            models.CheckConstraint(
                condition=Q(rate_to_rub__gt=0),
                name="calculator_currency_rate_positive",
            ),
        ]
        verbose_name = "Курс валюты"
        verbose_name_plural = "Курсы валют"

    def __str__(self) -> str:
        return f"{self.code} на {self.effective_date}: {self.rate_to_rub}"


class CustomsDutyRate(models.Model):
    """Ставка таможенной пошлины для автомобиля физического лица."""

    class AgeGroup(models.TextChoices):
        UP_TO_THREE = "up_to_3", "Не более 3 лет"
        THREE_TO_FIVE = "3_to_5", "Более 3, но не более 5 лет"
        OVER_FIVE = "over_5", "Более 5 лет"

    rate_version = models.ForeignKey(
        RateVersion,
        on_delete=models.CASCADE,
        related_name="customs_duty_rates",
        verbose_name="Версия ставок",
    )
    age_group = models.CharField(
        max_length=12,
        choices=AgeGroup.choices,
        verbose_name="Возраст автомобиля",
    )
    value_eur_min = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Стоимость от, евро",
    )
    value_eur_max = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Стоимость до, евро",
    )
    engine_capacity_min = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Объём двигателя от, см³",
    )
    engine_capacity_max = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Объём двигателя до, см³",
    )
    value_percentage = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Процент от стоимости",
    )
    minimum_eur_per_cc = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Минимум евро за см³",
    )
    fixed_eur_per_cc = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name="Евро за см³",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    notes = models.CharField(max_length=255, blank=True, verbose_name="Примечание")

    class Meta:
        ordering = ("rate_version", "age_group", "sort_order")
        indexes = [
            models.Index(
                fields=("rate_version", "age_group"),
                name="calc_customs_duty_lookup_idx",
            )
        ]
        verbose_name = "Ставка таможенной пошлины"
        verbose_name_plural = "Ставки таможенной пошлины"

    def __str__(self) -> str:
        return f"{self.rate_version.name}: {self.get_age_group_display()}"

    def clean(self) -> None:
        """Проверяет обязательные параметры формулы ставки."""
        super().clean()
        errors: dict[str, str] = {}

        if self.age_group == self.AgeGroup.UP_TO_THREE:
            if self.value_percentage is None:
                errors["value_percentage"] = "Укажите процент от стоимости."
            if self.minimum_eur_per_cc is None:
                errors["minimum_eur_per_cc"] = "Укажите минимум за см³."
        elif self.fixed_eur_per_cc is None:
            errors["fixed_eur_per_cc"] = "Укажите ставку за см³."

        if (
            self.value_eur_min is not None
            and self.value_eur_max is not None
            and self.value_eur_min > self.value_eur_max
        ):
            errors["value_eur_max"] = "Некорректный диапазон стоимости."

        if (
            self.engine_capacity_min is not None
            and self.engine_capacity_max is not None
            and self.engine_capacity_min > self.engine_capacity_max
        ):
            errors["engine_capacity_max"] = "Некорректный диапазон объёма."

        if errors:
            raise ValidationError(errors)


class CustomsClearanceFeeRate(models.Model):
    """Ставка сбора за таможенные операции."""

    rate_version = models.ForeignKey(
        RateVersion,
        on_delete=models.CASCADE,
        related_name="customs_clearance_fee_rates",
        verbose_name="Версия ставок",
    )
    customs_value_rub_min = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Таможенная стоимость от, ₽",
    )
    customs_value_rub_max = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Таможенная стоимость до, ₽",
    )
    fee_rub = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Сбор, ₽",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    notes = models.CharField(max_length=255, blank=True, verbose_name="Примечание")

    class Meta:
        ordering = ("rate_version", "sort_order")
        indexes = [
            models.Index(
                fields=("rate_version",),
                name="calc_customs_fee_lookup_idx",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(fee_rub__gte=0),
                name="calculator_customs_fee_nonnegative",
            )
        ]
        verbose_name = "Таможенный сбор"
        verbose_name_plural = "Таможенные сборы"

    def __str__(self) -> str:
        return f"{self.rate_version.name}: {self.fee_rub} ₽"

    def clean(self) -> None:
        """Проверяет диапазон таможенной стоимости."""
        super().clean()
        if (
            self.customs_value_rub_min is not None
            and self.customs_value_rub_max is not None
            and self.customs_value_rub_min > self.customs_value_rub_max
        ):
            raise ValidationError(
                {"customs_value_rub_max": "Некорректный диапазон стоимости."}
            )
