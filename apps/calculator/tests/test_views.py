"""Тесты страницы калькулятора."""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.calculator.models import (
    CalculatorDefinition,
    RateVersion,
    UtilizationRate,
)


class UtilizationFeeViewTests(TestCase):
    """Проверяет URL, форму и вывод результата."""

    @classmethod
    def setUpTestData(cls) -> None:
        calculator = CalculatorDefinition.objects.create(
            slug="util-sbor",
            title="Утилизационный сбор",
        )
        version = RateVersion.objects.create(
            calculator=calculator,
            name="Ставки 2026",
            effective_from=date(2026, 1, 1),
            effective_to=date(2026, 12, 31),
            base_rate=Decimal("20000"),
        )
        UtilizationRate.objects.create(
            rate_version=version,
            powertrain=UtilizationRate.Powertrain.COMBUSTION,
            usage_mode=UtilizationRate.UsageMode.PERSONAL,
            age_group=UtilizationRate.AgeGroup.NEW,
            engine_capacity_min=1001,
            engine_capacity_max=2000,
            power_kw_min=Decimal("95.62"),
            power_kw_max=Decimal("117.68"),
            coefficient=Decimal("0.17"),
        )
        UtilizationRate.objects.create(
            rate_version=version,
            powertrain=UtilizationRate.Powertrain.COMBUSTION,
            usage_mode=UtilizationRate.UsageMode.PERSONAL,
            age_group=UtilizationRate.AgeGroup.USED,
            engine_capacity_min=1001,
            engine_capacity_max=2000,
            power_kw_min=Decimal("95.62"),
            power_kw_max=Decimal("117.68"),
            coefficient=Decimal("0.26"),
        )

    def test_page_is_available(self) -> None:
        response = self.client.get(reverse("calculator:utilization_fee"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Калькулятор утилизационного сбора",
        )
        self.assertContains(
            response,
            "Свыше 1,0 до 2,0 л (1 001–2 000 см³)",
        )
        self.assertContains(
            response,
            "130–160 л.с. (95,62–117,68 кВт)",
        )

    def test_valid_form_displays_amount(self) -> None:
        response = self.client.post(
            reverse("calculator:utilization_fee"),
            {
                "powertrain": UtilizationRate.Powertrain.COMBUSTION,
                "age_group": UtilizationRate.AgeGroup.NEW,
                "engine_capacity_range": "1001:2000",
                "power_range": "95.62:117.68",
                "personal_use_confirmed": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3 400 ₽")
        self.assertContains(response, "5 200 ₽")
        self.assertContains(response, "Сравнение по возрасту автомобиля")

    def test_engine_capacity_is_required_for_combustion(self) -> None:
        response = self.client.post(
            reverse("calculator:utilization_fee"),
            {
                "powertrain": UtilizationRate.Powertrain.COMBUSTION,
                "age_group": UtilizationRate.AgeGroup.NEW,
                "power_range": "95.62:117.68",
                "personal_use_confirmed": "on",
            },
        )

        self.assertContains(
            response,
            "Выберите диапазон объёма двигателя.",
        )
