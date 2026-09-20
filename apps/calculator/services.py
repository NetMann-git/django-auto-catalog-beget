"""Сервисы расчёта утилизационного сбора."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q

from .models import CalculatorDefinition, RateVersion, UtilizationRate

HORSEPOWER_TO_KW = Decimal("0.73549875")
MONEY_STEP = Decimal("0.01")
UTILIZATION_CALCULATOR_SLUG = "util-sbor"


class RateConfigurationError(RuntimeError):
    """Ошибка конфигурации ставок."""


@dataclass(frozen=True, slots=True)
class UtilizationCalculationInput:
    """Параметры легкового автомобиля."""

    powertrain: str
    age_group: str
    power_kw: Decimal
    engine_capacity: int | None = None


@dataclass(frozen=True, slots=True)
class UtilizationCalculationResult:
    """Результат расчёта и применённая ставка."""

    amount: Decimal
    base_rate: Decimal
    coefficient: Decimal
    rate_version: RateVersion
    rate: UtilizationRate


def horsepower_to_kw(horsepower: Decimal) -> Decimal:
    """Переводит лошадиные силы в киловатты."""
    return horsepower * HORSEPOWER_TO_KW


def calculate_fee(base_rate: Decimal, coefficient: Decimal) -> Decimal:
    """Возвращает сумму сбора."""
    return (base_rate * coefficient).quantize(
        MONEY_STEP,
        rounding=ROUND_HALF_UP,
    )


class UtilizationFeeCalculator:
    """Рассчитывает сбор по действующему коэффициенту."""

    @classmethod
    def calculate(
        cls,
        data: UtilizationCalculationInput,
        *,
        calculation_date: date | None = None,
    ) -> UtilizationCalculationResult:
        """Рассчитывает сбор для автомобиля физлица."""
        actual_date = calculation_date or date.today()
        version = cls._get_rate_version(actual_date)
        rate = cls._get_rate(version, data)

        return UtilizationCalculationResult(
            amount=calculate_fee(version.base_rate, rate.coefficient),
            base_rate=version.base_rate,
            coefficient=rate.coefficient,
            rate_version=version,
            rate=rate,
        )

    @staticmethod
    def _get_rate_version(calculation_date: date) -> RateVersion:
        try:
            calculator = CalculatorDefinition.objects.get(
                slug=UTILIZATION_CALCULATOR_SLUG,
                is_active=True,
            )
        except CalculatorDefinition.DoesNotExist as error:
            raise RateConfigurationError(
                "Калькулятор утильсбора не опубликован."
            ) from error

        version = (
            calculator.rate_versions.filter(
                is_active=True,
                effective_from__lte=calculation_date,
            )
            .filter(
                Q(effective_to__isnull=True)
                | Q(effective_to__gte=calculation_date)
            )
            .order_by("-effective_from", "-id")
            .first()
        )
        if version is None:
            raise RateConfigurationError(
                "Для выбранной даты нет опубликованной версии ставок."
            )
        return version

    @staticmethod
    def _get_rate(
        version: RateVersion,
        data: UtilizationCalculationInput,
    ) -> UtilizationRate:
        rates = version.utilization_rates.filter(
            powertrain=data.powertrain,
            usage_mode=UtilizationRate.UsageMode.PERSONAL,
            age_group=data.age_group,
        ).filter(
            Q(power_kw_min__isnull=True) | Q(power_kw_min__lte=data.power_kw),
            Q(power_kw_max__isnull=True) | Q(power_kw_max__gte=data.power_kw),
        )

        if data.powertrain == UtilizationRate.Powertrain.COMBUSTION:
            if data.engine_capacity is None:
                raise ValueError(
                    "Для автомобиля с ДВС нужен объём двигателя."
                )
            rates = rates.filter(
                Q(engine_capacity_min__isnull=True)
                | Q(engine_capacity_min__lte=data.engine_capacity),
                Q(engine_capacity_max__isnull=True)
                | Q(engine_capacity_max__gte=data.engine_capacity),
            )
        else:
            rates = rates.filter(
                engine_capacity_min__isnull=True,
                engine_capacity_max__isnull=True,
            )

        matches = list(rates.order_by("sort_order", "id")[:2])
        if not matches:
            raise RateConfigurationError(
                "Для указанных параметров коэффициент не найден."
            )
        if len(matches) > 1:
            raise RateConfigurationError(
                "Для указанных параметров найдено несколько коэффициентов."
            )
        return matches[0]
