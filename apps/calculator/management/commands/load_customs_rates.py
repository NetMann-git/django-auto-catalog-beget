"""Загрузка ставок калькулятора растаможки из JSON-файла."""

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
    CurrencyRate,
    CustomsClearanceFeeRate,
    CustomsDutyRate,
    RateVersion,
)


class Command(BaseCommand):
    """Идемпотентно загружает ставки растаможки и курсы валют."""

    help = "Загружает ставки калькулятора растаможки из JSON-файла"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("file", type=Path, help="Путь к JSON-файлу")
        parser.add_argument(
            "--deactivate-overlapping",
            action="store_true",
            help="Отключить версии ставок с пересекающимся периодом",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Проверить файл без сохранения",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        payload = self._read_payload(options["file"])
        try:
            with transaction.atomic():
                version, duty_count, fee_count, currency_count = self._load(
                    payload,
                    deactivate_overlapping=options[
                        "deactivate_overlapping"
                    ],
                )
                if options["dry_run"]:
                    transaction.set_rollback(True)
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            raise CommandError(f"Некорректный файл ставок: {error}") from error

        action = "Проверено" if options["dry_run"] else "Загружено"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action}: {version.name}; пошлин: {duty_count}; "
                f"сборов: {fee_count}; валют: {currency_count}."
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
    ) -> tuple[RateVersion, int, int, int]:
        calculator_data = payload["calculator"]
        version_data = payload["rate_version"]
        duty_data = payload["duty_rates"]
        fee_data = payload["clearance_fee_rates"]
        currency_data = payload.get("currency_rates", [])

        if not duty_data or not fee_data:
            raise ValueError("Списки ставок не могут быть пустыми.")

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
        version, _ = RateVersion.objects.update_or_create(
            calculator=calculator,
            effective_from=effective_from,
            defaults={
                "name": version_data["name"],
                "effective_to": self._parse_date(
                    version_data.get("effective_to")
                ),
                "base_rate": version_data.get("base_rate", "0"),
                "source_name": version_data.get("source_name", ""),
                "source_url": version_data.get("source_url", ""),
                "notes": version_data.get("notes", ""),
                "is_active": version_data.get("is_active", True),
            },
        )

        if deactivate_overlapping and version.is_active:
            self._deactivate_overlapping(version)
        version.full_clean()
        version.save()

        duty_rates = [
            CustomsDutyRate(rate_version=version, **item)
            for item in duty_data
        ]
        fee_rates = [
            CustomsClearanceFeeRate(rate_version=version, **item)
            for item in fee_data
        ]
        for rate in [*duty_rates, *fee_rates]:
            rate.full_clean()

        version.customs_duty_rates.all().delete()
        version.customs_clearance_fee_rates.all().delete()
        CustomsDutyRate.objects.bulk_create(duty_rates)
        CustomsClearanceFeeRate.objects.bulk_create(fee_rates)

        for item in currency_data:
            code = item["code"].upper()
            effective_date = self._parse_date(item["effective_date"])
            currency = CurrencyRate.objects.filter(
                code=code,
                effective_date=effective_date,
            ).first() or CurrencyRate(
                code=code,
                effective_date=effective_date,
            )
            currency.nominal = item["nominal"]
            currency.rate_to_rub = item["rate_to_rub"]
            currency.source_url = item.get("source_url", "")
            currency.full_clean()
            currency.save()

        return version, len(duty_rates), len(fee_rates), len(currency_data)

    @staticmethod
    def _parse_date(value: str | date | None) -> date | None:
        if value is None or isinstance(value, date):
            return value
        return date.fromisoformat(value)

    @staticmethod
    def _deactivate_overlapping(version: RateVersion) -> None:
        overlapping = RateVersion.objects.filter(
            calculator=version.calculator,
            is_active=True,
        ).exclude(pk=version.pk)
        if version.effective_to:
            overlapping = overlapping.filter(
                effective_from__lte=version.effective_to
            )
        overlapping = overlapping.filter(
            Q(effective_to__isnull=True)
            | Q(effective_to__gte=version.effective_from)
        )
        overlapping.update(is_active=False)
