"""Тесты автоматического обновления официальных курсов валют."""

from datetime import date
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from apps.calculator.exchange_rates import (
    ExchangeRateError,
    refresh_current_rates,
    update_exchange_rates,
)
from apps.calculator.models import CurrencyRate


class _Response:
    """Контекстный менеджер для подмены ответа Банка России."""

    def __init__(self, content: bytes) -> None:
        self.content = content

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.content


def _xml(*, missing_krw: bool = False) -> bytes:
    krw = "" if missing_krw else (
        "<Valute><CharCode>KRW</CharCode><Nominal>1000</Nominal>"
        "<Value>60,99</Value></Valute>"
    )
    return (
        '<ValCurs Date="23.09.2026">'
        '<Valute><CharCode>USD</CharCode><Nominal>1</Nominal>'
        '<Value>84,19</Value></Valute>'
        '<Valute><CharCode>EUR</CharCode><Nominal>1</Nominal>'
        '<Value>96,66</Value></Valute>'
        '<Valute><CharCode>CNY</CharCode><Nominal>1</Nominal>'
        '<Value>12,56</Value></Valute>'
        f'{krw}</ValCurs>'
    ).encode()


class ExchangeRateTests(TestCase):
    """Проверяет загрузку, повторный вызов и отказоустойчивость."""

    def setUp(self) -> None:
        cache.clear()

    @patch("apps.calculator.exchange_rates.urlopen")
    def test_saves_rates_without_duplicates(self, opener: object) -> None:
        opener.return_value = _Response(_xml())
        for _ in range(2):
            self.assertEqual(
                update_exchange_rates(date(2026, 9, 23)),
                date(2026, 9, 23),
            )
        self.assertEqual(CurrencyRate.objects.count(), 5)
        self.assertEqual(CurrencyRate.objects.get(code="KRW").nominal, 1000)

    @patch("apps.calculator.exchange_rates.urlopen")
    def test_incomplete_response_does_not_change_database(
        self, opener: object
    ) -> None:
        opener.return_value = _Response(_xml(missing_krw=True))
        with self.assertRaises(ExchangeRateError):
            update_exchange_rates(date(2026, 9, 23))
        self.assertEqual(CurrencyRate.objects.count(), 0)

    @patch("apps.calculator.exchange_rates.update_exchange_rates")
    def test_only_one_request_within_cache_period(self, update: object) -> None:
        self.assertTrue(refresh_current_rates())
        self.assertTrue(refresh_current_rates())
        update.assert_called_once()

    @patch("apps.calculator.exchange_rates.update_exchange_rates")
    def test_failure_keeps_saved_rates(self, update: object) -> None:
        CurrencyRate.objects.create(
            code="EUR", nominal=1, rate_to_rub="96.66",
            effective_date=date(2026, 9, 19),
        )
        update.side_effect = ExchangeRateError("ЦБ недоступен")
        self.assertFalse(refresh_current_rates())
        self.assertFalse(refresh_current_rates())
        update.assert_called_once()
        self.assertEqual(CurrencyRate.objects.count(), 1)
