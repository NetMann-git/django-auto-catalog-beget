document.addEventListener("DOMContentLoaded", () => {
    const powertrain = document.getElementById("id_powertrain");
    const engineField = document.getElementById("customs-engine-field");
    const engineInput = document.getElementById("id_engine_capacity");
    const categoryNote = document.getElementById("customs-category-note");
    const powerHelp = document.getElementById("customs-power-help");

    if (!powertrain || !engineField || !engineInput) {
        return;
    }

    const updateFields = () => {
        const isElectric = powertrain.value === "electric";
        engineField.hidden = isElectric;
        engineInput.disabled = isElectric;
        engineInput.required = !isElectric;
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

    powertrain.addEventListener("change", updateFields);
    updateFields();
});
