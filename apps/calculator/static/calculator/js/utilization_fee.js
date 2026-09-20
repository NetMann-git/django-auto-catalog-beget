(function () {
    "use strict";

    const powertrain = document.getElementById("id_powertrain");
    const capacityField = document.querySelector(
        "[data-util-sbor-engine-capacity]"
    );
    const capacityInput = document.getElementById("id_engine_capacity");

    if (!powertrain || !capacityField || !capacityInput) {
        return;
    }

    function updateCapacityVisibility() {
        const isElectric = powertrain.value === "electric";
        capacityField.hidden = isElectric;
        capacityInput.disabled = isElectric;
        if (isElectric) {
            capacityInput.value = "";
        }
    }

    powertrain.addEventListener("change", updateCapacityVisibility);
    updateCapacityVisibility();
}());
