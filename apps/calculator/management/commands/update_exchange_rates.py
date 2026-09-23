"""Обновление курсов валют из официального XML Банка России."""

from datetime import date
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from apps.calculator.exchange_rates import ExchangeRateError, update_exchange_rates


class Command(BaseCommand):
    """Загружает официальные курсы валют Банка России в БД."""

    help = "Обновляет курсы валют по данным Банка России"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--date",
            dest="rate_date",
            type=date.fromisoformat,
            help="Дата курса в формате YYYY-MM-DD",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            effective_date = update_exchange_rates(
                options["rate_date"] or timezone.localdate(),
                timeout=20,
            )
        except ExchangeRateError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                f"Курсы на {effective_date:%d.%m.%Y} обновлены: 5 валют."
            )
        )
