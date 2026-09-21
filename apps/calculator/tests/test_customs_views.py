"""Тесты страницы калькулятора растаможки."""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.calculator.models import (
    CalculatorDefinition,
    CurrencyRate,
    CustomsAggregateRate,
    CustomsClearanceFeeRate,
    CustomsDutyRate,
    ExciseRate,
    RateVersion,
    UtilizationRate,
)


class CustomsClearanceViewTests(TestCase):
    """Проверяет URL, форму и результат растаможки."""

    @classmethod
    def setUpTestData(cls) -> None:
        customs = CalculatorDefinition.objects.create(
            slug="customs-clearance",
            title="Растаможка",
        )
        customs_version = RateVersion.objects.create(
            calculator=customs,
            name="Ставки 2026",
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
        CustomsAggregateRate.objects.create(
            rate_version=customs_version,
            powertrain=UtilizationRate.Powertrain.ELECTRIC,
            import_duty_percentage=Decimal("15"),
            vat_percentage=Decimal("22"),
        )
        ExciseRate.objects.create(
            rate_version=customs_version,
            power_hp_over=Decimal("90"),
            power_hp_up_to=Decimal("150"),
            rub_per_hp=Decimal("64"),
        )

        utilization = CalculatorDefinition.objects.create(
            slug="util-sbor",
            title="Утильсбор",
        )
        utilization_version = RateVersion.objects.create(
            calculator=utilization,
            name="Утильсбор 2026",
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
        UtilizationRate.objects.create(
            rate_version=utilization_version,
            powertrain=UtilizationRate.Powertrain.ELECTRIC,
            usage_mode=UtilizationRate.UsageMode.PERSONAL,
            age_group=UtilizationRate.AgeGroup.USED,
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

    def test_page_is_available(self) -> None:
        response = self.client.get(reverse("calculator:customs_clearance"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Калькулятор растаможки автомобилей")

    def test_valid_form_displays_total_and_breakdown(self) -> None:
        response = self.client.post(
            reverse("calculator:customs_clearance"),
            {
                "customs_value": "10000",
                "currency_code": "USD",
                "powertrain": UtilizationRate.Powertrain.COMBUSTION,
                "age_group": CustomsDutyRate.AgeGroup.THREE_TO_FIVE,
                "engine_capacity": "1500",
                "power_value": "150",
                "power_unit": "hp",
                "personal_use_confirmed": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "265 124 ₽")
        self.assertContains(response, "Ввозная пошлина")
        self.assertContains(response, "Утилизационный сбор")

    def test_electric_form_does_not_require_engine_capacity(self) -> None:
        response = self.client.post(
            reverse("calculator:customs_clearance"),
            {
                "customs_value": "10000",
                "currency_code": "USD",
                "powertrain": UtilizationRate.Powertrain.ELECTRIC,
                "age_group": CustomsDutyRate.AgeGroup.THREE_TO_FIVE,
                "power_value": "150",
                "power_unit": "hp",
                "personal_use_confirmed": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Укажите объём двигателя")
        self.assertContains(response, "384 536 ₽")
        self.assertContains(response, "Совокупный таможенный платёж")
