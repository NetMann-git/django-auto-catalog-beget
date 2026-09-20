"""Тесты команды загрузки ставок."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from apps.calculator.models import RateVersion, UtilizationRate


class LoadRatesCommandTests(TestCase):
    """Проверяет повторяемую загрузку ставок из JSON."""

    def test_command_replaces_rates_idempotently(self) -> None:
        payload = {
            "calculator": {
                "slug": "util-sbor",
                "title": "Калькулятор утилизационного сбора",
            },
            "rate_version": {
                "name": "Ставки 2026",
                "effective_from": "2026-01-01",
                "effective_to": "2026-12-31",
                "base_rate": "20000.00",
                "is_active": True,
            },
            "rates": [
                {
                    "powertrain": "combustion",
                    "usage_mode": "personal",
                    "age_group": "new",
                    "engine_capacity_min": 0,
                    "engine_capacity_max": 3000,
                    "power_kw_min": "0.00",
                    "power_kw_max": "117.68",
                    "coefficient": "0.1700",
                    "sort_order": 10,
                }
            ],
        }

        with TemporaryDirectory() as directory:
            file_path = Path(directory) / "rates.json"
            file_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            call_command("load_rates", file_path)
            call_command("load_rates", file_path)

        self.assertEqual(RateVersion.objects.count(), 1)
        self.assertEqual(UtilizationRate.objects.count(), 1)
