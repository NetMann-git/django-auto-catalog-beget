"""Тесты сервиса расчёта растаможки."""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.calculator.models import (
    CalculatorDefinition,
    CurrencyRate,
    CustomsClearanceFeeRate,
    CustomsDutyRate,
    RateVersion,
    UtilizationRate,
)
from apps.calculator.services import (
    CustomsCalculationInput,
    CustomsClearanceCalculator,
    horsepower_to_kw,
)


class CustomsClearanceCalculatorTests(TestCase):
    """Проверяет состав платежей и подбор ставок."""

    @classmethod
    def setUpTestData(cls) -> None:
        customs = CalculatorDefinition.objects.create(
            slug="customs-clearance",
            title="Растаможка",
        )
        customs_version = RateVersion.objects.create(
            calculator=customs,
            name="Тестовые ставки растаможки",
            effective_from=date(2026, 1, 1),
            effective_to=date(2026, 12, 31),
        )
        CustomsDutyRate.objects.create(
            rate_version=customs_version,
            age_group=CustomsDutyRate.AgeGroup.THREE_TO_FIVE,
            engine_capacity_min=1001,
            engine_capacity_max=1500,
            fixed_eur_per_cc=Decimal("1.7"),
        )
        CustomsClearanceFeeRate.objects.create(
            rate_version=customs_version,
            customs_value_rub_min=Decimal("450000.01"),
            customs_value_rub_max=Decimal("1200000"),
            fee_rub=Decimal("4924"),
        )

        utilization = CalculatorDefinition.objects.create(
            slug="util-sbor",
            title="Утильсбор",
        )
        utilization_version = RateVersion.objects.create(
            calculator=utilization,
            name="Тестовые ставки утильсбора",
            effective_from=date(2026, 1, 1),
            effective_to=date(2026, 12, 31),
            base_rate=Decimal("20000"),
        )
        UtilizationRate.objects.create(
            rate_version=utilization_version,
            powertrain=UtilizationRate.Powertrain.COMBUSTION,
            usage_mode=UtilizationRate.UsageMode.PERSONAL,
            age_group=UtilizationRate.AgeGroup.USED,
            engine_capacity_min=1001,
            engine_capacity_max=1500,
            power_kw_min=Decimal("0"),
            power_kw_max=Decimal("117.68"),
            coefficient=Decimal("0.26"),
        )

        for code, value in (("USD", "90"), ("EUR", "100")):
            CurrencyRate.objects.create(
                code=code,
                nominal=1,
                rate_to_rub=Decimal(value),
                effective_date=date(2026, 9, 19),
            )

    def test_calculate_returns_all_three_payments(self) -> None:
        result = CustomsClearanceCalculator.calculate(
            CustomsCalculationInput(
                customs_value=Decimal("10000"),
                currency_code="USD",
                age_group=CustomsDutyRate.AgeGroup.THREE_TO_FIVE,
                engine_capacity=1500,
                power_kw=horsepower_to_kw(Decimal("150")),
            ),
            calculation_date=date(2026, 9, 20),
        )

        self.assertEqual(result.customs_value_rub, Decimal("900000.00"))
        self.assertEqual(result.customs_duty, Decimal("255000.00"))
        self.assertEqual(result.clearance_fee, Decimal("4924.00"))
        self.assertEqual(result.utilization_fee, Decimal("5200.00"))
        self.assertEqual(result.total, Decimal("265124.00"))
