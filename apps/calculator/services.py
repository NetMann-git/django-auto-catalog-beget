"""Сервисы расчёта автомобильных платежей."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, TypeVar

from django.db.models import Q

from .models import (
    CalculatorDefinition,
    CurrencyRate,
    CustomsClearanceFeeRate,
    CustomsDutyRate,
    RateVersion,
    UtilizationRate,
)

HORSEPOWER_TO_KW = Decimal("0.73549875")
MONEY_STEP = Decimal("0.01")
UTILIZATION_CALCULATOR_SLUG = "util-sbor"
CUSTOMS_CALCULATOR_SLUG = "customs-clearance"
RateModel = TypeVar(
    "RateModel",
    CustomsDutyRate,
    CustomsClearanceFeeRate,
)


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


@dataclass(frozen=True, slots=True)
class CustomsCalculationInput:
    """Параметры автомобиля для расчёта таможенных платежей."""

    customs_value: Decimal
    currency_code: str
    age_group: str
    engine_capacity: int
    power_kw: Decimal


@dataclass(frozen=True, slots=True)
class CustomsCalculationResult:
    """Состав таможенных платежей в рублях."""

    customs_value_rub: Decimal
    customs_value_eur: Decimal
    customs_duty: Decimal
    clearance_fee: Decimal
    utilization_fee: Decimal
    total: Decimal
    duty_rate: CustomsDutyRate
    clearance_rate: CustomsClearanceFeeRate
    customs_rate_version: RateVersion
    utilization_result: UtilizationCalculationResult
    currency_rate: CurrencyRate
    eur_rate: CurrencyRate


def horsepower_to_kw(horsepower: Decimal) -> Decimal:
    """Переводит лошадиные силы в киловатты."""
    return horsepower * HORSEPOWER_TO_KW


def calculate_fee(base_rate: Decimal, coefficient: Decimal) -> Decimal:
    """Возвращает сумму сбора."""
    return (base_rate * coefficient).quantize(
        MONEY_STEP,
        rounding=ROUND_HALF_UP,
    )


def _get_rate_version(slug: str, calculation_date: date) -> RateVersion:
    """Возвращает опубликованную версию ставок на указанную дату."""
    try:
        calculator = CalculatorDefinition.objects.get(
            slug=slug,
            is_active=True,
        )
    except CalculatorDefinition.DoesNotExist as error:
        raise RateConfigurationError(
            "Калькулятор не опубликован."
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
        return _get_rate_version(
            UTILIZATION_CALCULATOR_SLUG,
            calculation_date,
        )

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


class CustomsClearanceCalculator:
    """Рассчитывает пошлину, таможенный сбор и утильсбор."""

    @classmethod
    def calculate(
        cls,
        data: CustomsCalculationInput,
        *,
        calculation_date: date | None = None,
    ) -> CustomsCalculationResult:
        """Возвращает детализацию платежей для автомобиля с ДВС."""
        actual_date = calculation_date or date.today()
        version = _get_rate_version(CUSTOMS_CALCULATOR_SLUG, actual_date)
        currency_rate = cls._get_currency_rate(
            data.currency_code,
            actual_date,
        )
        eur_rate = cls._get_currency_rate("EUR", actual_date)

        customs_value_rub = cls._to_rub(data.customs_value, currency_rate)
        eur_to_rub = eur_rate.rate_to_rub / Decimal(eur_rate.nominal)
        customs_value_eur = (customs_value_rub / eur_to_rub).quantize(
            MONEY_STEP,
            rounding=ROUND_HALF_UP,
        )

        duty_rate = cls._get_duty_rate(
            version,
            data,
            customs_value_eur,
        )
        duty_eur = cls._calculate_duty_eur(
            duty_rate,
            data,
            customs_value_eur,
        )
        customs_duty = (duty_eur * eur_to_rub).quantize(
            MONEY_STEP,
            rounding=ROUND_HALF_UP,
        )

        clearance_rate = cls._get_clearance_rate(
            version,
            customs_value_rub,
        )
        utilization_result = UtilizationFeeCalculator.calculate(
            UtilizationCalculationInput(
                powertrain=UtilizationRate.Powertrain.COMBUSTION,
                age_group=cls._utilization_age_group(data.age_group),
                engine_capacity=data.engine_capacity,
                power_kw=data.power_kw,
            ),
            calculation_date=actual_date,
        )
        total = (
            customs_duty
            + clearance_rate.fee_rub
            + utilization_result.amount
        ).quantize(MONEY_STEP, rounding=ROUND_HALF_UP)

        return CustomsCalculationResult(
            customs_value_rub=customs_value_rub,
            customs_value_eur=customs_value_eur,
            customs_duty=customs_duty,
            clearance_fee=clearance_rate.fee_rub,
            utilization_fee=utilization_result.amount,
            total=total,
            duty_rate=duty_rate,
            clearance_rate=clearance_rate,
            customs_rate_version=version,
            utilization_result=utilization_result,
            currency_rate=currency_rate,
            eur_rate=eur_rate,
        )

    @staticmethod
    def _get_currency_rate(code: str, actual_date: date) -> CurrencyRate:
        rate = (
            CurrencyRate.objects.filter(
                code=code.upper(),
                effective_date__lte=actual_date,
            )
            .order_by("-effective_date", "-id")
            .first()
        )
        if rate is None:
            raise RateConfigurationError(
                f"Не загружен курс валюты {code.upper()}."
            )
        return rate

    @staticmethod
    def _to_rub(amount: Decimal, rate: CurrencyRate) -> Decimal:
        value = amount * rate.rate_to_rub / Decimal(rate.nominal)
        return value.quantize(MONEY_STEP, rounding=ROUND_HALF_UP)

    @staticmethod
    def _get_duty_rate(
        version: RateVersion,
        data: CustomsCalculationInput,
        customs_value_eur: Decimal,
    ) -> CustomsDutyRate:
        rates = version.customs_duty_rates.filter(age_group=data.age_group)
        if data.age_group == CustomsDutyRate.AgeGroup.UP_TO_THREE:
            rates = rates.filter(
                Q(value_eur_min__isnull=True)
                | Q(value_eur_min__lte=customs_value_eur),
                Q(value_eur_max__isnull=True)
                | Q(value_eur_max__gte=customs_value_eur),
            )
        else:
            rates = rates.filter(
                Q(engine_capacity_min__isnull=True)
                | Q(engine_capacity_min__lte=data.engine_capacity),
                Q(engine_capacity_max__isnull=True)
                | Q(engine_capacity_max__gte=data.engine_capacity),
            )
        return CustomsClearanceCalculator._single_rate(
            rates.order_by("sort_order", "id")[:2],
            "ставка таможенной пошлины",
        )

    @staticmethod
    def _get_clearance_rate(
        version: RateVersion,
        customs_value_rub: Decimal,
    ) -> CustomsClearanceFeeRate:
        rates = version.customs_clearance_fee_rates.filter(
            Q(customs_value_rub_min__isnull=True)
            | Q(customs_value_rub_min__lte=customs_value_rub),
            Q(customs_value_rub_max__isnull=True)
            | Q(customs_value_rub_max__gte=customs_value_rub),
        )
        return CustomsClearanceCalculator._single_rate(
            rates.order_by("sort_order", "id")[:2],
            "ставка таможенного сбора",
        )

    @staticmethod
    def _single_rate(
        rates: Iterable[RateModel],
        rate_name: str,
    ) -> RateModel:
        matches = list(rates)
        if not matches:
            raise RateConfigurationError(f"Не найдена {rate_name}.")
        if len(matches) > 1:
            raise RateConfigurationError(
                f"Найдено несколько значений: {rate_name}."
            )
        return matches[0]

    @staticmethod
    def _calculate_duty_eur(
        rate: CustomsDutyRate,
        data: CustomsCalculationInput,
        customs_value_eur: Decimal,
    ) -> Decimal:
        if rate.age_group == CustomsDutyRate.AgeGroup.UP_TO_THREE:
            if (
                rate.value_percentage is None
                or rate.minimum_eur_per_cc is None
            ):
                raise RateConfigurationError(
                    "Не заполнена формула таможенной пошлины."
                )
            percentage_amount = (
                customs_value_eur
                * rate.value_percentage
                / Decimal("100")
            )
            minimum_amount = (
                Decimal(data.engine_capacity)
                * rate.minimum_eur_per_cc
            )
            return max(percentage_amount, minimum_amount)

        if rate.fixed_eur_per_cc is None:
            raise RateConfigurationError(
                "Не заполнена ставка пошлины за см³."
            )
        return Decimal(data.engine_capacity) * rate.fixed_eur_per_cc

    @staticmethod
    def _utilization_age_group(customs_age_group: str) -> str:
        if customs_age_group == CustomsDutyRate.AgeGroup.UP_TO_THREE:
            return UtilizationRate.AgeGroup.NEW
        return UtilizationRate.AgeGroup.USED
