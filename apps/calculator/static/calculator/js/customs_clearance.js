document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".customs-calc__form");
    if (form) {
        form.addEventListener("submit", () => {
            // После входа в аккаунт Django меняет CSRF-cookie; форма могла
            // остаться открытой со старым токеном.
            const token = form.querySelector('[name="csrfmiddlewaretoken"]');
            const currentToken = getCookie("csrftoken");
            if (token && currentToken) {
                token.value = currentToken;
            }
        });
    }

    const powertrain = document.getElementById("id_powertrain");
    const engineField = document.getElementById("customs-engine-field");
    const engineInput = document.getElementById("id_engine_capacity");
    const categoryNote = document.getElementById("customs-category-note");
    const powerHelp = document.getElementById("customs-power-help");

    if (
        !powertrain
        || !engineField
        || !engineInput
    ) {
        return;
    }

    const updateFields = () => {
        const isElectric = powertrain.value === "electric";
        engineField.hidden = isElectric;
        engineInput.disabled = isElectric;
        engineInput.required = !isElectric;
        if (isElectric) {
            engineInput.value = "";
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

    powertrain.addEventListener("change", updateFields);
    updateFields();
});
