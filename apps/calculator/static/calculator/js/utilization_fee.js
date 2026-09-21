(function () {
    "use strict";

    const powertrain = document.getElementById("id_powertrain");
    const capacityField = document.querySelector(
        "[data-util-sbor-engine-capacity]"
    );
    const capacitySelect = document.getElementById(
        "id_engine_capacity_range"
    );
    const powerSelect = document.getElementById("id_power_range");
    const optionsData = document.getElementById(
        "util-sbor-power-options"
    );

    if (
        !powertrain
        || !capacityField
        || !capacitySelect
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

    function updateCapacityVisibility() {
        const isElectric = powertrain.value === "electric";
        capacityField.hidden = isElectric;
        capacitySelect.disabled = isElectric;

        if (isElectric) {
            capacitySelect.value = "";
        }
    }

    function updatePowerOptions() {
        const previousValue = powerSelect.value;
        const options = powerOptions[powertrain.value] || [];

        powerSelect.replaceChildren();
        powerSelect.add(new Option("Выберите диапазон мощности", ""));

        options.forEach(function (item) {
            powerSelect.add(new Option(item.label, item.value));
        });

        if (options.some(function (item) {
            return item.value === previousValue;
        })) {
            powerSelect.value = previousValue;
        }
    }

    powertrain.addEventListener("change", function () {
        updateCapacityVisibility();
        updatePowerOptions();
    });

    updateCapacityVisibility();
}());
