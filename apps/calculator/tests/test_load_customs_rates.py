"""Тесты загрузки официальных ставок растаможки."""

from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from apps.calculator.models import (
    CurrencyRate,
    CustomsAggregateRate,
    CustomsClearanceFeeRate,
    CustomsDutyRate,
    ExciseRate,
)


class LoadCustomsRatesCommandTests(TestCase):
    """Проверяет полный файл ставок и идемпотентность команды."""

    def test_command_loads_fixture_idempotently(self) -> None:
        fixture = (
            Path(__file__).resolve().parents[1]
            / "fixtures"
            / "customs_2026.json"
        )

        call_command("load_customs_rates", fixture)
        call_command("load_customs_rates", fixture)

        self.assertEqual(CustomsDutyRate.objects.count(), 18)
        self.assertEqual(CustomsAggregateRate.objects.count(), 1)
        self.assertEqual(ExciseRate.objects.count(), 7)
        self.assertEqual(CustomsClearanceFeeRate.objects.count(), 8)
        self.assertEqual(CurrencyRate.objects.count(), 5)
