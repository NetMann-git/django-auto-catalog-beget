"""Загрузка версионируемых ставок калькулятора из JSON-файла."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.db.models import Q

from apps.calculator.models import (
    CalculatorDefinition,
    RateVersion,
    UtilizationRate,
)


class Command(BaseCommand):
    """Идемпотентно загружает версию ставок и заменяет её коэффициенты."""

    help = "Загружает ставки калькулятора из JSON-файла"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("file", type=Path, help="Путь к JSON-файлу ставок")
        parser.add_argument(
            "--deactivate-overlapping",
            action="store_true",
            help="Отключить опубликованные версии с пересекающимся периодом",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Проверить файл без сохранения изменений",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        payload = self._read_payload(options["file"])

        try:
            with transaction.atomic():
                rate_version, rate_count = self._load(
                    payload,
                    deactivate_overlapping=options["deactivate_overlapping"],
                )
                if options["dry_run"]:
                    transaction.set_rollback(True)
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            raise CommandError(f"Некорректный файл ставок: {error}") from error

        action = "Проверено" if options["dry_run"] else "Загружено"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action}: {rate_version.name}; коэффициентов: {rate_count}."
            )
        )

    @staticmethod
    def _read_payload(file_path: Path) -> dict[str, Any]:
        if not file_path.is_file():
            raise CommandError(f"Файл не найден: {file_path}")

        try:
            with file_path.open(encoding="utf-8") as source:
                payload = json.load(source)
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError(f"Не удалось прочитать JSON: {error}") from error

        if not isinstance(payload, dict):
            raise CommandError("Корневой элемент JSON должен быть объектом.")
        return payload

    def _load(
        self,
        payload: dict[str, Any],
        *,
        deactivate_overlapping: bool,
    ) -> tuple[RateVersion, int]:
        calculator_data = payload["calculator"]
        version_data = payload["rate_version"]
        rates_data = payload["rates"]

        if not isinstance(rates_data, list) or not rates_data:
            raise ValueError("Поле rates должно содержать непустой список.")

        calculator, _ = CalculatorDefinition.objects.update_or_create(
            slug=calculator_data["slug"],
            defaults={
                "title": calculator_data["title"],
                "description": calculator_data.get("description", ""),
                "is_active": calculator_data.get("is_active", True),
                "sort_order": calculator_data.get("sort_order", 0),
            },
        )

        effective_from = self._parse_date(version_data["effective_from"])
        rate_version, _ = RateVersion.objects.update_or_create(
            calculator=calculator,
            effective_from=effective_from,
            defaults={
                "name": version_data["name"],
                "effective_to": self._parse_date(version_data.get("effective_to")),
                "base_rate": version_data["base_rate"],
                "source_name": version_data.get("source_name", ""),
                "source_url": version_data.get("source_url", ""),
                "notes": version_data.get("notes", ""),
                "is_active": version_data.get("is_active", True),
            },
        )

        if deactivate_overlapping and rate_version.is_active:
            self._deactivate_overlapping(rate_version)

        rate_version.full_clean()
        rate_version.save()

        rates = [
            UtilizationRate(rate_version=rate_version, **rate_data)
            for rate_data in rates_data
        ]
        for rate in rates:
            rate.full_clean()

        rate_version.utilization_rates.all().delete()
        UtilizationRate.objects.bulk_create(rates)
        return rate_version, len(rates)

    @staticmethod
    def _parse_date(value: str | date | None) -> date | None:
        if value is None or isinstance(value, date):
            return value
        return date.fromisoformat(value)

    @staticmethod
    def _deactivate_overlapping(rate_version: RateVersion) -> None:
        period_end = rate_version.effective_to
        overlapping = RateVersion.objects.filter(
            calculator=rate_version.calculator,
            is_active=True,
        ).exclude(pk=rate_version.pk)

        if period_end:
            overlapping = overlapping.filter(effective_from__lte=period_end)
        overlapping = overlapping.filter(
            Q(effective_to__isnull=True)
            | Q(effective_to__gte=rate_version.effective_from)
        )
        overlapping.update(is_active=False)
