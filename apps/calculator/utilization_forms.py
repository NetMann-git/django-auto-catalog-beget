"""Форма утильсбора с диапазонами из опубликованных ставок."""

from decimal import Decimal, ROUND_HALF_UP

from django import forms

from .models import RateVersion, UtilizationRate
from .services import kw_to_horsepower


def _token(lower: int | Decimal | None, upper: int | Decimal | None) -> str:
    lower_value = "" if lower is None else str(lower)
    upper_value = "" if upper is None else str(upper)
    return f"{lower_value}:{upper_value}"


def _unique_ranges(
    values: list[tuple[object | None, object | None]],
) -> list[tuple[object | None, object | None]]:
    result: list[tuple[object | None, object | None]] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _decimal_label(value: Decimal) -> str:
    return format(value, "f").rstrip("0").rstrip(".").replace(".", ",")


def _capacity_label(lower: int | None, upper: int | None) -> str:
    if lower is not None and upper is None:
        liters = str(
            (Decimal(lower - 1) / Decimal("1000")).quantize(Decimal("0.0"))
        ).replace(".", ",")
        capacity = f"{lower:,}".replace(",", " ")
        return f"Свыше {liters} л (от {capacity} см³)"

    if upper is None:
        return "Любой объём"

    upper_liters = str(
        (Decimal(upper) / Decimal("1000")).quantize(Decimal("0.0"))
    ).replace(".", ",")
    upper_capacity = f"{upper:,}".replace(",", " ")
    if lower is None or lower <= 1:
        return f"До {upper_liters} л (до {upper_capacity} см³)"

    lower_liters = str(
        (Decimal(lower - 1) / Decimal("1000")).quantize(Decimal("0.0"))
    ).replace(".", ",")
    capacity = f"{lower:,}–{upper:,}".replace(",", " ")
    return (
        f"Свыше {lower_liters} до {upper_liters} л "
        f"({capacity} см³)"
    )


def _horsepower_label(value: Decimal) -> Decimal:
    return kw_to_horsepower(value).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )


def _power_label(lower: Decimal | None, upper: Decimal | None) -> str:
    if lower is None and upper is not None:
        return (
            f"До {_horsepower_label(upper)} л.с. "
            f"(до {_decimal_label(upper)} кВт)"
        )
    if lower is not None and upper is None:
        return (
            f"От {_horsepower_label(lower)} л.с. "
            f"(от {_decimal_label(lower)} кВт)"
        )
    if lower is None or upper is None:
        return "Любая мощность"
    return (
        f"{_horsepower_label(lower)}–{_horsepower_label(upper)} л.с. "
        f"({_decimal_label(lower)}–{_decimal_label(upper)} кВт)"
    )


class UtilizationFeeForm(forms.Form):
    """Параметры автомобиля в виде официальных диапазонов."""

    powertrain = forms.ChoiceField(
        label="Тип силовой установки",
        choices=UtilizationRate.Powertrain.choices,
        initial=UtilizationRate.Powertrain.COMBUSTION,
    )
    engine_capacity_range = forms.ChoiceField(
        label="Объём двигателя",
        choices=(),
        required=False,
        help_text="Выберите диапазон по точному объёму из документов автомобиля.",
    )
    power_range = forms.ChoiceField(
        label="Мощность двигателя",
        choices=(),
        help_text=(
            "Числа в л. с. округлены для удобства, поэтому соседние "
            "диапазоны могут выглядеть пересекающимися (например, "
            "250–280 и 280–310 л. с.). Выбирайте диапазон по точной "
            "мощности в кВт из ЭПТС: 205,94 кВт относится к первому, "
            "205,95 кВт — ко второму. Если в документах указаны только "
            "л. с., уточните мощность в кВт перед выбором."
        ),
    )
    age_group = forms.ChoiceField(
        label="Возраст автомобиля",
        choices=UtilizationRate.AgeGroup.choices,
        initial=UtilizationRate.AgeGroup.NEW,
    )
    personal_use_confirmed = forms.BooleanField(
        label=(
            "Подтверждаю ввоз физическим лицом для личного пользования "
            "и соблюдение условий применения ставок"
        ),
        required=True,
    )

    def __init__(
        self,
        *args: object,
        rate_version: RateVersion | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.power_choices_by_powertrain: dict[str, list[dict[str, str]]] = {}
        if rate_version is None:
            unavailable = [("", "Ставки временно недоступны")]
            self.fields["engine_capacity_range"].choices = unavailable
            self.fields["power_range"].choices = unavailable
            return

        capacities = list(
            rate_version.utilization_rates.filter(
                powertrain=UtilizationRate.Powertrain.COMBUSTION,
                usage_mode=UtilizationRate.UsageMode.PERSONAL,
            )
            .order_by("engine_capacity_min", "engine_capacity_max")
            .values_list("engine_capacity_min", "engine_capacity_max")
        )
        self.fields["engine_capacity_range"].choices = [
            ("", "Выберите объём двигателя"),
            *[
                (_token(lower, upper), _capacity_label(lower, upper))
                for lower, upper in _unique_ranges(capacities)
            ],
        ]

        for powertrain, _label in UtilizationRate.Powertrain.choices:
            ranges = list(
                rate_version.utilization_rates.filter(
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
        power_choices = self.power_choices_by_powertrain.get(selected, [])
        self.fields["power_range"].choices = [
            ("", "Выберите диапазон мощности"),
            *[(item["value"], item["label"]) for item in power_choices],
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
        cleaned_data = super().clean()
        powertrain = cleaned_data.get("powertrain")
        capacity_token = cleaned_data.get("engine_capacity_range")
        power_token = cleaned_data.get("power_range")

        if powertrain == UtilizationRate.Powertrain.COMBUSTION:
            if not capacity_token:
                self.add_error(
                    "engine_capacity_range",
                    "Выберите диапазон объёма двигателя.",
                )
            else:
                cleaned_data["engine_capacity"] = self._representative(
                    str(capacity_token),
                    int,
                )
        else:
            cleaned_data["engine_capacity"] = None

        if power_token:
            cleaned_data["power_kw"] = self._representative(
                str(power_token),
                Decimal,
            )
        return cleaned_data

    def selected_label(self, field_name: str) -> str:
        value = self.cleaned_data.get(field_name)
        return dict(self.fields[field_name].choices).get(str(value), "")
