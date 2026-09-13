(() => {
    "use strict";

    document.querySelectorAll(".client-delete-form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const name = form.dataset.clientName || "клиента";
            if (!window.confirm(`Удалить карточку «${name}»? Это действие нельзя отменить.`)) {
                event.preventDefault();
            }
        });
    });

    const grid = document.getElementById("client-sortable");
    if (!grid || !grid.dataset.reorderUrl) return;

    const status = document.getElementById("client-sort-status");
    const csrfToken = grid.dataset.csrfToken || "";
    let draggedCard = null;
    let saveTimer = null;

    const cards = () => [...grid.querySelectorAll(".client-admin-card")];

    const setStatus = (text, className = "") => {
        if (!status) return;
        status.textContent = text;
        status.className = `client-sort-status ${className}`.trim();
    };

    const updateOrderLabels = () => {
        cards().forEach((card, index) => {
            const label = card.querySelector(".client-order-value");
            if (label) label.textContent = String((index + 1) * 10);
        });
    };

    const saveOrder = async () => {
        const ids = cards().map((card) => card.dataset.clientId).filter(Boolean);
        setStatus("Сохраняю…", "is-saving");

        try {
            const response = await fetch(grid.dataset.reorderUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: new URLSearchParams({ordered_ids: ids.join(",")}).toString(),
                credentials: "same-origin",
            });

            let data = null;
            try {
                data = await response.json();
            } catch (_) {
                throw new Error(`Сервер вернул HTTP ${response.status}. Обновите страницу.`);
            }

            if (!response.ok || !data.ok) {
                throw new Error(data.error || `Ошибка HTTP ${response.status}`);
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
        saveTimer = window.setTimeout(saveOrder, 120);
    };

    grid.querySelectorAll(".client-admin-card__drag").forEach((handle) => {
        const card = handle.closest(".client-admin-card");
        if (!card) return;

        handle.addEventListener("dragstart", (event) => {
            draggedCard = card;
            card.classList.add("is-dragging");
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", card.dataset.clientId || "");
        });

        handle.addEventListener("dragend", () => {
            card.classList.remove("is-dragging");
            cards().forEach((item) => item.classList.remove("is-drag-over"));
            draggedCard = null;
        });
    });

    cards().forEach((card) => {
        card.addEventListener("dragover", (event) => {
            if (!draggedCard || draggedCard === card) return;
            event.preventDefault();
            event.dataTransfer.dropEffect = "move";
            card.classList.add("is-drag-over");
        });

        card.addEventListener("dragleave", () => card.classList.remove("is-drag-over"));

        card.addEventListener("drop", (event) => {
            if (!draggedCard || draggedCard === card) return;
            event.preventDefault();
            card.classList.remove("is-drag-over");

            const currentCards = cards();
            const draggedIndex = currentCards.indexOf(draggedCard);
            const targetIndex = currentCards.indexOf(card);

            if (draggedIndex < targetIndex) {
                card.insertAdjacentElement("afterend", draggedCard);
            } else {
                card.insertAdjacentElement("beforebegin", draggedCard);
            }

            updateOrderLabels();
            queueSave();
        });
    });
})();
