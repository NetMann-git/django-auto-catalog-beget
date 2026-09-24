"""Формы пользовательских калькуляторов."""

from datetime import date
from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import (
    CustomsDutyRate,
    UtilizationRate,
)
from .services import horsepower_to_kw


class UtilizationFeeForm(forms.Form):
    """Параметры автомобиля, ввозимого физическим лицом."""

    POWER_UNIT_HORSEPOWER = "hp"
    POWER_UNIT_KILOWATTS = "kw"
    POWER_UNIT_CHOICES = (
        (POWER_UNIT_HORSEPOWER, "л. с."),
        (POWER_UNIT_KILOWATTS, "кВт"),
    )

    powertrain = forms.ChoiceField(
        label="Тип силовой установки",
        choices=UtilizationRate.Powertrain.choices,
    )
    age_group = forms.ChoiceField(
        label="Возраст автомобиля",
        choices=UtilizationRate.AgeGroup.choices,
    )
    engine_capacity = forms.IntegerField(
        label="Объём двигателя, см³",
        min_value=1,
        max_value=20000,
        required=False,
        help_text=(
            "Для электромобиля поле не заполняется."
        ),
    )
    power_value = forms.DecimalField(
        label="Мощность",
        min_value=Decimal("0.01"),
        max_value=Decimal("5000"),
        max_digits=8,
        decimal_places=2,
    )
    power_unit = forms.ChoiceField(
        label="Единица мощности",
        choices=POWER_UNIT_CHOICES,
        initial=POWER_UNIT_HORSEPOWER,
    )
    personal_use_confirmed = forms.BooleanField(
        label=(
            "Подтверждаю ввоз физическим лицом для личного "
            "пользования "
            "и соблюдение условий применения ставок"
        ),
        required=True,
    )

    def clean(self) -> dict[str, object]:
        """Проверяет объём и добавляет мощность в кВт."""
        cleaned_data = super().clean()
        powertrain = cleaned_data.get("powertrain")
        engine_capacity = cleaned_data.get("engine_capacity")

        if (
            powertrain == UtilizationRate.Powertrain.COMBUSTION
            and engine_capacity is None
        ):
            self.add_error(
                "engine_capacity",
                "Укажите объём двигателя.",
            )

        if powertrain == UtilizationRate.Powertrain.ELECTRIC:
            cleaned_data["engine_capacity"] = None

        power_value = cleaned_data.get("power_value")
        power_unit = cleaned_data.get("power_unit")
        if isinstance(power_value, Decimal):
            cleaned_data["power_kw"] = (
                horsepower_to_kw(power_value)
                if power_unit == self.POWER_UNIT_HORSEPOWER
                else power_value
            )

        return cleaned_data


class CustomsClearanceForm(forms.Form):
    """Параметры растаможки легкового автомобиля физического лица."""

    CURRENCY_LABELS = {
        "RUB": "Российский рубль (RUB)",
        "USD": "Доллар США (USD)",
        "EUR": "Евро (EUR)",
        "CNY": "Китайский юань (CNY)",
        "KRW": "Южнокорейская вона (KRW)",
    }
    ALLOWED_CURRENCIES = ("RUB", "USD", "EUR", "CNY", "KRW")
    POWERTRAIN_CHOICES = (
        (UtilizationRate.Powertrain.COMBUSTION, "ДВС или параллельный гибрид"),
        (UtilizationRate.Powertrain.ELECTRIC,
         "Электромобиль или последовательный гибрид"),
    )

    powertrain = forms.ChoiceField(
        label="Тип силовой установки",
        choices=POWERTRAIN_CHOICES,
    )

    customs_value = forms.DecimalField(
        label="Таможенная стоимость",
        min_value=Decimal("0.01"),
        max_digits=16,
        decimal_places=2,
        help_text="Цена автомобиля и расходы до границы ЕАЭС.",
    )
    currency_code = forms.ChoiceField(
        label="Валюта стоимости",
        choices=(),
    )
    age_group = forms.ChoiceField(
        label="Возраст автомобиля",
        choices=CustomsDutyRate.AgeGroup.choices,
    )
    calculation_date = forms.DateField(
        label="Дата расчёта",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Используются ставки и курсы, действующие на эту дату.",
    )
    engine_capacity = forms.IntegerField(
        label="Точный объём двигателя, см³",
        min_value=1,
        max_value=20000,
        required=False,
        help_text=(
            "Укажите рабочий объём из ЭПТС или документов автомобиля."
        ),
    )
    power_value = forms.DecimalField(
        label="Точная мощность",
        min_value=Decimal("0.01"),
        max_value=Decimal("5000"),
        max_digits=8,
        decimal_places=2,
        help_text=(
            "Для EV укажите максимальную 30-минутную мощность из ЭПТС."
        ),
    )
    power_unit = forms.ChoiceField(
        label="Единица мощности",
        choices=UtilizationFeeForm.POWER_UNIT_CHOICES,
        initial=UtilizationFeeForm.POWER_UNIT_HORSEPOWER,
    )
    personal_use_confirmed = forms.BooleanField(
        label=(
            "Подтверждаю ввоз физическим лицом для личного "
            "пользования и соблюдение условий применения ставок"
        ),
        required=True,
    )

    def __init__(
        self,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Показывает все поддерживаемые валюты даже до загрузки курса."""
        super().__init__(*args, **kwargs)
        self.fields["currency_code"].choices = [
            (code, self.CURRENCY_LABELS.get(code, code))
            for code in self.ALLOWED_CURRENCIES
        ]
        self.fields["currency_code"].initial = "USD"

    def clean_calculation_date(self) -> date:
        """Не разрешает расчёт по ещё не действующим ставкам."""
        calculation_date = self.cleaned_data["calculation_date"]
        if calculation_date > timezone.localdate():
            raise forms.ValidationError(
                "Дата расчёта не может быть позднее текущей даты."
            )
        return calculation_date

    def clean(self) -> dict[str, object]:
        """Проверяет точные параметры и приводит мощность к нужным единицам."""
        cleaned_data = super().clean()
        powertrain = cleaned_data.get("powertrain")
        engine_capacity = cleaned_data.get("engine_capacity")
        if (
            powertrain == UtilizationRate.Powertrain.COMBUSTION
            and engine_capacity is None
        ):
            self.add_error(
                "engine_capacity",
                "Укажите точный объём двигателя.",
            )
        elif powertrain == UtilizationRate.Powertrain.ELECTRIC:
            cleaned_data["engine_capacity"] = None

        power_value = cleaned_data.get("power_value")
        power_unit = cleaned_data.get("power_unit")
        if isinstance(power_value, Decimal):
            if power_unit == UtilizationFeeForm.POWER_UNIT_HORSEPOWER:
                cleaned_data["power_hp"] = power_value
                cleaned_data["power_kw"] = horsepower_to_kw(power_value)
            else:
                cleaned_data["power_kw"] = power_value
                cleaned_data["power_hp"] = power_value / Decimal("0.75")
        return cleaned_data
