"""Формы пользовательских калькуляторов."""

from decimal import Decimal

from django import forms

from .models import UtilizationRate
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
