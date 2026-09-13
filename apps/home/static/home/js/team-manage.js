(() => {
    "use strict";

    document.querySelectorAll(".team-delete-form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const name = form.dataset.memberName || "сотрудника";
            if (!window.confirm(`Удалить сотрудника «${name}»? Это действие нельзя отменить.`)) event.preventDefault();
        });
    });

    const grid = document.getElementById("team-sortable");
    if (!grid || !grid.dataset.reorderUrl) return;

    const status = document.getElementById("team-sort-status");
    const csrfToken = grid.dataset.csrfToken || "";
    let draggedCard = null;
    let saveTimer = null;
    const cards = () => [...grid.querySelectorAll(".client-admin-card")];
    const setStatus = (text, className = "") => { if (status) { status.textContent = text; status.className = `client-sort-status ${className}`.trim(); } };
    const updateOrderLabels = () => cards().forEach((card, index) => { const label = card.querySelector(".team-order-value"); if (label) label.textContent = String((index + 1) * 10); });

    const saveOrder = async () => {
        const ids = cards().map((card) => card.dataset.memberId).filter(Boolean);
        setStatus("Сохраняю…", "is-saving");
        try {
            const response = await fetch(grid.dataset.reorderUrl, {
                method: "POST",
                headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8", "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest"},
                body: new URLSearchParams({ordered_ids: ids.join(",")}).toString(),
                credentials: "same-origin",
            });
            const data = await response.json();
            if (!response.ok || !data.ok) throw new Error(data.error || `Ошибка HTTP ${response.status}`);
            updateOrderLabels();
            setStatus("Порядок сохранён", "is-saved");
            window.setTimeout(() => setStatus(""), 1800);
        } catch (error) { setStatus(error.message || "Ошибка сохранения", "is-error"); }
    };
    const queueSave = () => { window.clearTimeout(saveTimer); saveTimer = window.setTimeout(saveOrder, 120); };

    grid.querySelectorAll(".client-admin-card__drag").forEach((handle) => {
        const card = handle.closest(".client-admin-card");
        if (!card) return;
        handle.addEventListener("dragstart", (event) => { draggedCard = card; card.classList.add("is-dragging"); event.dataTransfer.effectAllowed = "move"; event.dataTransfer.setData("text/plain", card.dataset.memberId || ""); });
        handle.addEventListener("dragend", () => { card.classList.remove("is-dragging"); cards().forEach((item) => item.classList.remove("is-drag-over")); draggedCard = null; });
    });

    cards().forEach((card) => {
        card.addEventListener("dragover", (event) => { if (!draggedCard || draggedCard === card) return; event.preventDefault(); event.dataTransfer.dropEffect = "move"; card.classList.add("is-drag-over"); });
        card.addEventListener("dragleave", () => card.classList.remove("is-drag-over"));
        card.addEventListener("drop", (event) => {
            if (!draggedCard || draggedCard === card) return;
            event.preventDefault(); card.classList.remove("is-drag-over");
            const current = cards(); const from = current.indexOf(draggedCard); const to = current.indexOf(card);
            if (from < to) card.insertAdjacentElement("afterend", draggedCard); else card.insertAdjacentElement("beforebegin", draggedCard);
            updateOrderLabels(); queueSave();
        });
    });
})();
