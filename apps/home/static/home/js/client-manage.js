(() => {
    "use strict";

    const deleteForms = document.querySelectorAll(".client-delete-form");
    deleteForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            const name = form.dataset.clientName || "клиента";
            if (!window.confirm(`Удалить карточку «${name}»? Это действие нельзя отменить.`)) {
                event.preventDefault();
            }
        });
    });

    const grid = document.getElementById("client-sortable");
    if (!grid || !grid.dataset.reorderUrl) {
        return;
    }

    const status = document.getElementById("client-sort-status");
    let dragged = null;
    let saveTimer = null;

    const getCsrfToken = () => {
        const input = document.querySelector("input[name='csrfmiddlewaretoken']");
        return input ? input.value : "";
    };

    const updateOrderLabels = () => {
        [...grid.querySelectorAll(".client-admin-card")].forEach((card, index) => {
            const label = card.querySelector(".client-order-value");
            if (label) {
                label.textContent = String((index + 1) * 10);
            }
        });
    };

    const setStatus = (text, className = "") => {
        if (!status) return;
        status.textContent = text;
        status.className = `client-sort-status ${className}`.trim();
    };

    const saveOrder = async () => {
        const ids = [...grid.querySelectorAll(".client-admin-card")]
            .map((card) => card.dataset.clientId)
            .filter(Boolean);

        const body = new URLSearchParams({ordered_ids: ids.join(",")});
        setStatus("Сохраняю…", "is-saving");

        try {
            const response = await fetch(grid.dataset.reorderUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "X-CSRFToken": getCsrfToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: body.toString(),
                credentials: "same-origin",
            });

            const data = await response.json();
            if (!response.ok || !data.ok) {
                throw new Error(data.error || "Не удалось сохранить порядок.");
            }

            updateOrderLabels();
            setStatus("Порядок сохранён", "is-saved");
            window.setTimeout(() => setStatus(""), 1800);
        } catch (error) {
            setStatus(error.message || "Ошибка сохранения", "is-error");
        }
    };

    const queueSave = () => {
        window.clearTimeout(saveTimer);
        saveTimer = window.setTimeout(saveOrder, 180);
    };

    grid.querySelectorAll(".client-admin-card").forEach((card) => {
        const handle = card.querySelector(".client-admin-card__drag");
        if (handle) {
            handle.addEventListener("mousedown", () => {
                card.dataset.dragArmed = "1";
            });
        }

        card.addEventListener("dragstart", (event) => {
            if (card.dataset.dragArmed !== "1") {
                event.preventDefault();
                return;
            }

            delete card.dataset.dragArmed;
            dragged = card;
            card.classList.add("is-dragging");
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", card.dataset.clientId || "");
        });

        card.addEventListener("dragend", () => {
            delete card.dataset.dragArmed;
            card.classList.remove("is-dragging");
            grid.querySelectorAll(".client-admin-card").forEach((item) => item.classList.remove("is-drag-over"));
            dragged = null;
        });

        card.addEventListener("dragover", (event) => {
            if (!dragged || dragged === card) return;
            event.preventDefault();
            card.classList.add("is-drag-over");
            event.dataTransfer.dropEffect = "move";
        });

        card.addEventListener("dragleave", () => {
            card.classList.remove("is-drag-over");
        });

        card.addEventListener("drop", (event) => {
            if (!dragged || dragged === card) return;
            event.preventDefault();
            card.classList.remove("is-drag-over");

            const rect = card.getBoundingClientRect();
            const insertAfter = event.clientY > rect.top + rect.height / 2;
            grid.insertBefore(dragged, insertAfter ? card.nextSibling : card);
            queueSave();
        });
    });
})();
