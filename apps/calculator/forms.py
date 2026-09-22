"""Формы пользовательских калькуляторов."""

from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import (
    CurrencyRate,
    CustomsDutyRate,
    RateVersion,
    UtilizationRate,
)
from .services import horsepower_to_kw
from .utilization_forms import (
    _capacity_label,
    _power_label,
    _token,
    _unique_ranges,
)


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

    powertrain = forms.ChoiceField(
        label="Тип силовой установки",
        choices=UtilizationRate.Powertrain.choices,
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
    engine_capacity_range = forms.ChoiceField(
        label="Объём двигателя",
        choices=(),
        required=False,
        help_text=(
            "Выберите диапазон по объёму из документов автомобиля. "
            "Расчёт выполняется по верхней границе диапазона."
        ),
    )
    power_range = forms.ChoiceField(
        label="Мощность",
        choices=(),
        help_text=(
            "Выберите диапазон мощности. Для EV используется максимальная "
            "30-минутная мощность из ЭПТС. Расчёт выполняется по верхней "
            "границе диапазона."
        ),
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
        utilization_rate_version: RateVersion | None = None,
        **kwargs: object,
    ) -> None:
        """Заполняет валюты и диапазоны из опубликованных ставок."""
        super().__init__(*args, **kwargs)
        self.power_choices_by_powertrain: dict[
            str,
            list[dict[str, str]],
        ] = {}
        available_codes = set(
            CurrencyRate.objects.filter(
                effective_date__lte=timezone.localdate(),
            ).values_list("code", flat=True)
        )
        choices = [
            (code, self.CURRENCY_LABELS.get(code, code))
            for code in self.ALLOWED_CURRENCIES
            if code in available_codes
        ]
        self.fields["currency_code"].choices = choices
        if "USD" in available_codes:
            self.fields["currency_code"].initial = "USD"

        if utilization_rate_version is None:
            unavailable = [("", "Ставки временно недоступны")]
            self.fields["engine_capacity_range"].choices = unavailable
            self.fields["power_range"].choices = unavailable
            return

        capacities = list(
            utilization_rate_version.utilization_rates.filter(
                powertrain=UtilizationRate.Powertrain.COMBUSTION,
                usage_mode=UtilizationRate.UsageMode.PERSONAL,
            )
            .order_by("engine_capacity_min", "engine_capacity_max")
            .values_list("engine_capacity_min", "engine_capacity_max")
        )
        self.fields["engine_capacity_range"].choices = [
            ("", "Выберите диапазон объёма"),
            *[
                (_token(lower, upper), _capacity_label(lower, upper))
                for lower, upper in _unique_ranges(capacities)
            ],
        ]

        for powertrain, _label in UtilizationRate.Powertrain.choices:
            ranges = list(
                utilization_rate_version.utilization_rates.filter(
                    powertrain=powertrain,
                    usage_mode=UtilizationRate.UsageMode.PERSONAL,
                )
                .order_by("power_kw_min", "power_kw_max")
                .values_list("power_kw_min", "power_kw_max")
            )
            self.power_choices_by_powertrain[powertrain] = [
                {
                    "value": _token(lower, upper),
                    "label": _power_label(lower, upper),
                }
                for lower, upper in _unique_ranges(ranges)
            ]

        selected = self._selected_powertrain()
        selected_power_ranges = self.power_choices_by_powertrain.get(
            selected,
            [],
        )
        self.fields["power_range"].choices = [
            ("", "Выберите диапазон мощности"),
            *[
                (item["value"], item["label"])
                for item in selected_power_ranges
            ],
        ]

    def _selected_powertrain(self) -> str:
        if self.is_bound:
            value = self.data.get(self.add_prefix("powertrain"))
            if value:
                return str(value)
        return UtilizationRate.Powertrain.COMBUSTION

    @staticmethod
    def _representative(token: str, value_type: type) -> object | None:
        lower_value, upper_value = token.split(":", maxsplit=1)
        lower = value_type(lower_value) if lower_value else None
        upper = value_type(upper_value) if upper_value else None
        return upper if upper is not None else lower

    def clean(self) -> dict[str, object]:
        """Проверяет поля и добавляет мощность в кВт и л. с."""
        cleaned_data = super().clean()
        powertrain = cleaned_data.get("powertrain")
        capacity_token = cleaned_data.get("engine_capacity_range")
        if (
            powertrain == UtilizationRate.Powertrain.COMBUSTION
            and not capacity_token
        ):
            self.add_error(
                "engine_capacity_range",
                "Выберите диапазон объёма двигателя.",
            )
        elif powertrain == UtilizationRate.Powertrain.COMBUSTION:
            cleaned_data["engine_capacity"] = self._representative(
                str(capacity_token),
                int,
            )
        else:
            cleaned_data["engine_capacity"] = None

        power_token = cleaned_data.get("power_range")
        if power_token:
            power_kw = self._representative(str(power_token), Decimal)
            if isinstance(power_kw, Decimal):
                cleaned_data["power_kw"] = power_kw
                cleaned_data["power_hp"] = power_kw / Decimal("0.75")
        return cleaned_data

    def selected_label(self, field_name: str) -> str:
        value = self.cleaned_data.get(field_name)
        return dict(self.fields[field_name].choices).get(str(value), "")
