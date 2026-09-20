"""Обновление курсов валют из официального XML Банка России."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from xml.etree import ElementTree

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.calculator.models import CurrencyRate

CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"


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
        requested_date = options["rate_date"] or date.today()
        request_url = (
            f"{CBR_URL}?date_req={requested_date.strftime('%d/%m/%Y')}"
        )
        try:
            with urlopen(request_url, timeout=20) as response:
                content = response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            raise CommandError(
                f"Не удалось получить курсы Банка России: {error}"
            ) from error

        try:
            root = ElementTree.fromstring(content)
            effective_date = datetime.strptime(
                root.attrib["Date"],
                "%d.%m.%Y",
            ).date()
        except (ElementTree.ParseError, KeyError, ValueError) as error:
            raise CommandError(f"Некорректный ответ Банка России: {error}") from error

        rates = [
            {
                "code": "RUB",
                "nominal": 1,
                "rate_to_rub": Decimal("1"),
            }
        ]
        for node in root.findall("Valute"):
            code = node.findtext("CharCode")
            nominal = node.findtext("Nominal")
            value = node.findtext("Value")
            if not code or not nominal or not value:
                continue
            rates.append(
                {
                    "code": code,
                    "nominal": int(nominal),
                    "rate_to_rub": Decimal(value.replace(",", ".")),
                }
            )

        with transaction.atomic():
            for rate in rates:
                CurrencyRate.objects.update_or_create(
                    code=rate["code"],
                    effective_date=effective_date,
                    defaults={
                        "nominal": rate["nominal"],
                        "rate_to_rub": rate["rate_to_rub"],
                        "source_url": CBR_URL,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Курсы на {effective_date:%d.%m.%Y} обновлены: "
                f"{len(rates)} валют."
            )
        )
