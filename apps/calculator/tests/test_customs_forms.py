"""Тесты формы калькулятора растаможки."""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.calculator.forms import CustomsClearanceForm
from apps.calculator.models import (
    CalculatorDefinition,
    CurrencyRate,
    RateVersion,
    UtilizationRate,
)


class CustomsClearanceFormTests(TestCase):
    """Проверяет категории силовой установки и список валют."""

    @classmethod
    def setUpTestData(cls) -> None:
        for code in ("RUB", "USD", "EUR", "CNY", "KRW", "GBP"):
            CurrencyRate.objects.create(
                code=code,
                nominal=1,
                rate_to_rub=Decimal("1"),
                effective_date=date(2026, 1, 1),
            )
        calculator = CalculatorDefinition.objects.create(
            slug="util-sbor",
            title="Утильсбор",
        )
        cls.rate_version = RateVersion.objects.create(
            calculator=calculator,
            name="Ставки 2026",
            effective_from=date(2026, 1, 1),
            effective_to=date(2026, 12, 31),
            base_rate=Decimal("20000"),
        )
        for powertrain, capacity_min, capacity_max in (
            (UtilizationRate.Powertrain.COMBUSTION, 1001, 2000),
            (UtilizationRate.Powertrain.ELECTRIC, None, None),
        ):
            UtilizationRate.objects.create(
                rate_version=cls.rate_version,
                powertrain=powertrain,
                usage_mode=UtilizationRate.UsageMode.PERSONAL,
                age_group=UtilizationRate.AgeGroup.NEW,
                engine_capacity_min=capacity_min,
                engine_capacity_max=capacity_max,
                power_kw_min=Decimal("95.62"),
                power_kw_max=Decimal("117.68"),
                coefficient=Decimal("0.17"),
            )

    def test_only_supported_currencies_are_available(self) -> None:
        form = CustomsClearanceForm(
            utilization_rate_version=self.rate_version,
        )

        self.assertEqual(
            [code for code, _label in form.fields["currency_code"].choices],
            ["RUB", "USD", "EUR", "CNY", "KRW"],
        )

    def test_combustion_requires_engine_capacity(self) -> None:
        form = CustomsClearanceForm(
            data={
                "powertrain": UtilizationRate.Powertrain.COMBUSTION,
                "customs_value": "10000",
                "currency_code": "USD",
                "age_group": "3_to_5",
                "power_range": "95.62:117.68",
                "personal_use_confirmed": "on",
            },
            utilization_rate_version=self.rate_version,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("engine_capacity_range", form.errors)

    def test_electric_ignores_engine_capacity(self) -> None:
        form = CustomsClearanceForm(
            data={
                "powertrain": UtilizationRate.Powertrain.ELECTRIC,
                "customs_value": "10000",
                "currency_code": "USD",
                "age_group": "3_to_5",
                "engine_capacity_range": "1001:2000",
                "power_range": "95.62:117.68",
                "personal_use_confirmed": "on",
            },
            utilization_rate_version=self.rate_version,
        )

        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["engine_capacity"])

    def test_ranges_use_upper_boundary_for_calculation(self) -> None:
        form = CustomsClearanceForm(
            data={
                "powertrain": UtilizationRate.Powertrain.COMBUSTION,
                "customs_value": "10000",
                "currency_code": "USD",
                "age_group": "3_to_5",
                "engine_capacity_range": "1001:2000",
                "power_range": "95.62:117.68",
                "personal_use_confirmed": "on",
            },
            utilization_rate_version=self.rate_version,
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["engine_capacity"], 2000)
        self.assertEqual(form.cleaned_data["power_kw"], Decimal("117.68"))
