"""Представления раздела калькуляторов."""

from decimal import Decimal
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .forms import UtilizationFeeForm
from .services import (
    RateConfigurationError,
    UtilizationCalculationInput,
    UtilizationFeeCalculator,
)


def _format_money(value: Decimal) -> str:
    """Форматирует денежную сумму."""
    return f"{value:,.0f}".replace(",", " ")


def utilization_fee(request: HttpRequest) -> HttpResponse:
    """Показывает форму и результат расчёта."""
    form = UtilizationFeeForm(request.POST or None)
    context: dict[str, Any] = {"form": form}

    if request.method == "POST" and form.is_valid():
        try:
            result = UtilizationFeeCalculator.calculate(
                UtilizationCalculationInput(
                    powertrain=str(form.cleaned_data["powertrain"]),
                    age_group=str(form.cleaned_data["age_group"]),
                    engine_capacity=form.cleaned_data["engine_capacity"],
                    power_kw=form.cleaned_data["power_kw"],
                )
            )
        except RateConfigurationError as error:
            context["configuration_error"] = str(error)
        else:
            context.update(
                {
                    "result": result,
                    "formatted_amount": _format_money(result.amount),
                    "formatted_base_rate": _format_money(result.base_rate),
                }
            )

    return render(request, "calculator/utilization_fee.html", context)
