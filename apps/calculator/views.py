"""Представления раздела калькуляторов."""

from decimal import Decimal
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .forms import CustomsClearanceForm, UtilizationFeeForm
from .services import (
    CustomsCalculationInput,
    CustomsClearanceCalculator,
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


def customs_clearance(request: HttpRequest) -> HttpResponse:
    """Показывает форму и результат расчёта растаможки."""
    form = CustomsClearanceForm(request.POST or None)
    context: dict[str, Any] = {"form": form}

    if request.method == "POST" and form.is_valid():
        try:
            result = CustomsClearanceCalculator.calculate(
                CustomsCalculationInput(
                    customs_value=form.cleaned_data["customs_value"],
                    currency_code=str(form.cleaned_data["currency_code"]),
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
                    "formatted_total": _format_money(result.total),
                    "formatted_duty": _format_money(result.customs_duty),
                    "formatted_clearance_fee": _format_money(
                        result.clearance_fee
                    ),
                    "formatted_utilization_fee": _format_money(
                        result.utilization_fee
                    ),
                    "formatted_value_rub": _format_money(
                        result.customs_value_rub
                    ),
                }
            )

    return render(request, "calculator/customs_clearance.html", context)
