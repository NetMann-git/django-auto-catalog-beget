document.addEventListener("DOMContentLoaded", () => {
    const powertrain = document.getElementById("id_powertrain");
    const engineField = document.getElementById("customs-engine-field");
    const engineSelect = document.getElementById("id_engine_capacity_range");
    const powerSelect = document.getElementById("id_power_range");
    const optionsData = document.getElementById("customs-power-options");
    const categoryNote = document.getElementById("customs-category-note");
    const powerHelp = document.getElementById("customs-power-help");

    if (
        !powertrain
        || !engineField
        || !engineSelect
        || !powerSelect
        || !optionsData
    ) {
        return;
    }

    let powerOptions = {};
    try {
        powerOptions = JSON.parse(optionsData.textContent);
    } catch (error) {
        return;
    }

    const updatePowerOptions = () => {
        const previousValue = powerSelect.value;
        const options = powerOptions[powertrain.value] || [];
        powerSelect.replaceChildren();
        powerSelect.add(new Option("Выберите диапазон мощности", ""));
        options.forEach((item) => {
            powerSelect.add(new Option(item.label, item.value));
        });
        if (options.some((item) => item.value === previousValue)) {
            powerSelect.value = previousValue;
        }
    };

    const updateFields = () => {
        const isElectric = powertrain.value === "electric";
        engineField.hidden = isElectric;
        engineSelect.disabled = isElectric;
        engineSelect.required = !isElectric;
        if (isElectric) {
            engineSelect.value = "";
        }
        if (isElectric) {
            categoryNote.textContent =
                "Для EV и последовательного гибрида применяется совокупный " +
                "платёж: ввозная пошлина, акциз и НДС. Объём генератора не нужен.";
            powerHelp.textContent =
                "Укажите максимальную 30-минутную мощность из ЭПТС.";
        } else {
            categoryNote.textContent =
                "Для ДВС и параллельного гибрида применяется единая ставка " +
                "физического лица по возрасту, стоимости и объёму двигателя.";
            powerHelp.textContent =
                "Мощность нужна для расчёта утилизационного сбора.";
        }
    };

    powertrain.addEventListener("change", () => {
        updateFields();
        updatePowerOptions();
    });
    updateFields();
});
