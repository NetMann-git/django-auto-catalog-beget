"""Тесты формы калькулятора растаможки."""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.calculator.forms import CustomsClearanceForm
from apps.calculator.models import CurrencyRate, UtilizationRate


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

    def test_only_supported_currencies_are_available(self) -> None:
        form = CustomsClearanceForm()

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
                "power_value": "150",
                "power_unit": "hp",
                "personal_use_confirmed": "on",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("engine_capacity", form.errors)

    def test_electric_ignores_engine_capacity(self) -> None:
        form = CustomsClearanceForm(
            data={
                "powertrain": UtilizationRate.Powertrain.ELECTRIC,
                "customs_value": "10000",
                "currency_code": "USD",
                "age_group": "3_to_5",
                "engine_capacity": "1500",
                "power_value": "150",
                "power_unit": "hp",
                "personal_use_confirmed": "on",
            }
        )

        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["engine_capacity"])
