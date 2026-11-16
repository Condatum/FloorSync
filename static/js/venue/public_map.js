(function () {
    const dialog = document.getElementById("table-detail-dialog");
    if (!dialog) return;

    const titleEl = document.getElementById("dialog-table-title");
    const subtitleEl = document.getElementById("dialog-table-subtitle");
    const zoneEl = document.getElementById("dialog-table-zone");
    const statusEl = document.getElementById("dialog-table-status");
    const capacityEl = document.getElementById("dialog-table-capacity");
    const minSpendEl = document.getElementById("dialog-table-min-spend");
    const perksEl = document.getElementById("dialog-table-perks");
    const connectLink = document.getElementById("dialog-connect-link");

    document.querySelectorAll("[data-table-trigger]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const code = btn.dataset.code || "";
            const label = btn.dataset.label || code;
            titleEl.textContent = label !== code ? `${code} — ${label}` : `Table ${code}`;
            subtitleEl.textContent = "Real-time floor table metadata & direct concierge routing";
            zoneEl.textContent = btn.dataset.zone || "—";
            statusEl.textContent = btn.dataset.status || "—";
            capacityEl.textContent = btn.dataset.capacity || "—";
            minSpendEl.textContent = btn.dataset.minSpend || "—";
            perksEl.textContent = btn.dataset.perks || "Standard Seating";
            connectLink.href = btn.dataset.deeplink || "#";
            dialog.showModal();
        });
    });

    // Safari / legacy fallback for <dialog closedby="any">
    if (!("closedBy" in HTMLDialogElement.prototype)) {
        dialog.addEventListener("click", (event) => {
            if (event.target !== dialog) return;
            const rect = dialog.getBoundingClientRect();
            const isDialogContent = (
                rect.top <= event.clientY &&
                event.clientY <= rect.top + rect.height &&
                rect.left <= event.clientX &&
                event.clientX <= rect.left + rect.width
            );
            if (isDialogContent) return;
            dialog.close();
        });
    }
})();
