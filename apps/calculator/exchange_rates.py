"""Обновление курсов Банка России без привязки к хостингу."""

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from xml.etree import ElementTree

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .models import CurrencyRate

CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
REQUIRED_CODES = {"USD", "EUR", "CNY", "KRW"}
LOGGER = logging.getLogger(__name__)


class ExchangeRateError(RuntimeError):
    """Не удалось получить корректные курсы ЦБ."""


def update_exchange_rates(rate_date: date, *, timeout: int = 5) -> date:
    """Проверяет ответ ЦБ и атомарно сохраняет нужные валюты."""
    request_url = f"{CBR_URL}?date_req={rate_date:%d/%m/%Y}"
    try:
        with urlopen(request_url, timeout=timeout) as response:
            root = ElementTree.fromstring(response.read())
        effective_date = datetime.strptime(
            root.attrib["Date"], "%d.%m.%Y"
        ).date()
        if effective_date > rate_date:
            raise ExchangeRateError("ЦБ вернул курс из будущего.")

        rates = {}
        for node in root.findall("Valute"):
            code = node.findtext("CharCode")
            if code not in REQUIRED_CODES:
                continue
            nominal = int(node.findtext("Nominal") or "")
            value = Decimal((node.findtext("Value") or "").replace(",", "."))
            if nominal < 1 or value <= 0:
                raise ExchangeRateError("ЦБ вернул недопустимый курс.")
            rates[code] = (nominal, value)
        if rates.keys() != REQUIRED_CODES:
            raise ExchangeRateError("В ответе ЦБ отсутствуют необходимые валюты.")
    except (HTTPError, URLError, TimeoutError, OSError, ElementTree.ParseError,
            KeyError, ValueError, InvalidOperation) as error:
        raise ExchangeRateError(f"Не удалось получить курсы ЦБ: {error}") from error

    rates["RUB"] = (1, Decimal("1"))
    with transaction.atomic():
        for code, (nominal, value) in rates.items():
            CurrencyRate.objects.update_or_create(
                code=code,
                effective_date=effective_date,
                defaults={
                    "nominal": nominal,
                    "rate_to_rub": value,
                    "source_url": CBR_URL,
                },
            )
    return effective_date


def refresh_current_rates() -> bool:
    """Пробует обновить курс раз в 6 часов; сбой не прерывает расчёт."""
    today = timezone.localdate()
    key = f"calculator:cbr:checked:{today.isoformat()}"
    cached_result = cache.get(key)
    if cached_result is not None:
        return cached_result == "ok"
    lock_key = f"calculator:cbr:lock:{today.isoformat()}"
    if not cache.add(lock_key, True, timeout=15):
        return False
    try:
        try:
            update_exchange_rates(today)
        except ExchangeRateError:
            LOGGER.warning("Не удалось обновить курсы ЦБ", exc_info=True)
            cache.set(key, "failed", timeout=900)
            return False
        cache.set(key, "ok", timeout=21600)
        return True
    finally:
        cache.delete(lock_key)
