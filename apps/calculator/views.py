"""Представления раздела калькуляторов."""

from decimal import Decimal
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .forms import CustomsClearanceForm
from .models import RateVersion, UtilizationRate
from .services import (
    CustomsCalculationInput,
    CustomsClearanceCalculator,
    RateConfigurationError,
    UtilizationCalculationInput,
    UtilizationFeeCalculator,
)
from .utilization_forms import UtilizationFeeForm


def _format_money(value: Decimal) -> str:
    """Форматирует денежную сумму."""
    return f"{value:,.0f}".replace(",", " ")


def _utilization_input(
    form: UtilizationFeeForm,
    *,
    age_group: str,
) -> UtilizationCalculationInput:
    """Создаёт входные данные сервиса из проверенной формы."""
    return UtilizationCalculationInput(
        powertrain=str(form.cleaned_data["powertrain"]),
        age_group=age_group,
        engine_capacity=form.cleaned_data["engine_capacity"],
        power_kw=form.cleaned_data["power_kw"],
    )


def _comparison_results(
    form: UtilizationFeeForm,
    rate_version: RateVersion,
) -> list[dict[str, object]]:
    """Рассчитывает обе возрастные ставки для сравнения."""
    selected_age = str(form.cleaned_data["age_group"])
    results: list[dict[str, object]] = []
    for age_group, label in UtilizationRate.AgeGroup.choices:
        calculation = UtilizationFeeCalculator.calculate(
            _utilization_input(form, age_group=age_group),
            rate_version=rate_version,
        )
        results.append(
            {
                "label": label,
                "formatted_amount": _format_money(calculation.amount),
                "is_selected": age_group == selected_age,
            }
        )
    return results


def utilization_fee(request: HttpRequest) -> HttpResponse:
    """Показывает форму, итоговый расчёт и сравнение по возрасту."""
    context: dict[str, Any] = {}
    try:
        rate_version = UtilizationFeeCalculator.get_rate_version()
    except RateConfigurationError as error:
        rate_version = None
        context["configuration_error"] = str(error)

    form = UtilizationFeeForm(
        request.POST or None,
        rate_version=rate_version,
    )
    context.update(
        {
            "form": form,
            "rate_version": rate_version,
            "power_choices_by_powertrain": (
                form.power_choices_by_powertrain
            ),
        }
    )

    if (
        request.method == "POST"
        and rate_version is not None
        and form.is_valid()
    ):
        try:
            result = UtilizationFeeCalculator.calculate(
                _utilization_input(
                    form,
                    age_group=str(form.cleaned_data["age_group"]),
                ),
                rate_version=rate_version,
            )
            comparison_results = _comparison_results(form, rate_version)
        except RateConfigurationError as error:
            context["configuration_error"] = str(error)
        else:
            context.update(
                {
                    "result": result,
                    "formatted_amount": _format_money(result.amount),
                    "formatted_base_rate": _format_money(result.base_rate),
                    "comparison_results": comparison_results,
                    "selected_capacity_label": form.selected_label(
                        "engine_capacity_range"
                    ),
                    "selected_power_label": form.selected_label("power_range"),
                }
            )

    return render(request, "calculator/utilization_fee.html", context)


def customs_clearance(request: HttpRequest) -> HttpResponse:
    """Показывает форму и результат расчёта растаможки."""
    form = CustomsClearanceForm(request.POST or None)
    context: dict[str, Any] = {"form": form}
    try:
        rate_version = CustomsClearanceCalculator.get_rate_version()
    except RateConfigurationError as error:
        rate_version = None
        context["configuration_error"] = str(error)
    context["rate_version"] = rate_version

    if (
        request.method == "POST"
        and rate_version is not None
        and form.is_valid()
    ):
        try:
            result = CustomsClearanceCalculator.calculate(
                CustomsCalculationInput(
                    customs_value=form.cleaned_data["customs_value"],
                    currency_code=str(form.cleaned_data["currency_code"]),
                    powertrain=str(form.cleaned_data["powertrain"]),
                    age_group=str(form.cleaned_data["age_group"]),
                    engine_capacity=form.cleaned_data["engine_capacity"],
                    power_kw=form.cleaned_data["power_kw"],
                    power_hp=form.cleaned_data["power_hp"],
                ),
                rate_version=rate_version,
            )
        except RateConfigurationError as error:
            context["configuration_error"] = str(error)
        else:
            context.update(
                {
                    "result": result,
                    "formatted_total": _format_money(result.total),
                    "formatted_duty": _format_money(result.customs_duty),
                    "formatted_excise": _format_money(result.excise),
                    "formatted_vat": _format_money(result.vat),
                    "formatted_aggregate_payment": _format_money(
                        result.aggregate_customs_payment
                    ),
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
