(function () {
    const root = document.querySelector("[data-floor-map-root]");
    const dialog = document.getElementById("table-detail-dialog");
    if (!dialog) return;

    const titleEl = document.getElementById("dialog-table-title");
    const subtitleEl = document.getElementById("dialog-table-subtitle");
    const zoneEl = document.getElementById("dialog-table-zone");
    const statusEl = document.getElementById("dialog-table-status");
    const capacityEl = document.getElementById("dialog-table-capacity");
    const minSpendEl = document.getElementById("dialog-table-min-spend");
    const perksEl = document.getElementById("dialog-table-perks");
    const notesRowEl = document.getElementById("dialog-notes-row");
    const notesEl = document.getElementById("dialog-table-notes");
    const connectLink = document.getElementById("dialog-connect-link");

    const zoneSelect = document.getElementById("filter-zone");
    const statusSelect = document.getElementById("filter-status");
    const capacitySelect = document.getElementById("filter-capacity");
    const resetBtn = document.getElementById("btn-reset-filters");
    const refreshBtn = document.getElementById("btn-refresh-floor");
    const matchSummary = document.getElementById("filter-match-summary");
    const lastSyncedLabel = document.getElementById("last-synced-label");

    const tableButtons = Array.from(document.querySelectorAll("[data-table-trigger]"));
    let activeDialogTableId = null;

    function populateDialog(btn) {
        const code = btn.dataset.code || "";
        const label = btn.dataset.label || code;
        titleEl.textContent = label !== code ? `${code} — ${label}` : `Table ${code}`;
        subtitleEl.textContent = "Real-time floor table metadata & direct concierge routing";
        zoneEl.textContent = btn.dataset.zone || "—";
        statusEl.textContent = btn.dataset.status || "—";
        capacityEl.textContent = btn.dataset.capacity || "—";
        minSpendEl.textContent = btn.dataset.minSpend || "—";
        perksEl.textContent = btn.dataset.perks || "Standard Seating";
        const notes = (btn.dataset.notes || "").trim();
        if (notesRowEl && notesEl) {
            notesRowEl.hidden = !notes;
            notesEl.textContent = notes || "—";
        }
        connectLink.href = btn.dataset.deeplink || "#";
    }

    tableButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            activeDialogTableId = btn.dataset.tableId || null;
            populateDialog(btn);
            dialog.showModal();
        });
    });

    dialog.addEventListener("close", () => {
        activeDialogTableId = null;
        dialog.returnValue = "";
    });

    function applyFilters() {
        const zoneVal = zoneSelect ? zoneSelect.value : "ALL";
        const statusVal = statusSelect ? statusSelect.value : "ALL";
        const minCap = capacitySelect ? parseInt(capacitySelect.value, 10) || 0 : 0;

        let matched = 0;
        tableButtons.forEach((btn) => {
            const matchesZone = zoneVal === "ALL" || btn.dataset.zoneId === zoneVal;
            const matchesStatus = statusVal === "ALL" || btn.dataset.statusCode === statusVal;
            const cap = parseInt(btn.dataset.capacityNum || "0", 10);
            const matchesCap = cap >= minCap;
            const isMatch = matchesZone && matchesStatus && matchesCap;

            btn.dataset.dimmed = isMatch ? "false" : "true";
            if (isMatch) matched += 1;
        });

        if (matchSummary) {
            const total = tableButtons.length;
            if (zoneVal === "ALL" && statusVal === "ALL" && minCap === 0) {
                matchSummary.textContent = `Showing all ${total} visible tables.`;
            } else {
                matchSummary.textContent = `Highlighted ${matched} of ${total} tables matching your filters.`;
            }
        }
    }

    [zoneSelect, statusSelect, capacitySelect].forEach((ctrl) => {
        if (ctrl) ctrl.addEventListener("change", applyFilters);
    });

    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            if (zoneSelect) zoneSelect.value = "ALL";
            if (statusSelect) statusSelect.value = "ALL";
            if (capacitySelect) capacitySelect.value = "0";
            applyFilters();
        });
    }

    const STATUS_CLASSES = ["status-AVAILABLE", "status-RESERVED", "status-OCCUPIED", "status-BLOCKED"];

    async function syncFloorStatus() {
        const apiUrl = root && root.dataset.statusApi;
        if (!apiUrl) return;

        try {
            const resp = await fetch(apiUrl, { headers: { Accept: "application/json" } });
            if (!resp.ok) return;
            const data = await resp.json();

            const countMap = {
                "count-available": data.counts?.available,
                "count-reserved": data.counts?.reserved,
                "count-occupied": data.counts?.occupied,
                "count-blocked": data.counts?.blocked,
            };
            Object.entries(countMap).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el && typeof val === "number") el.textContent = String(val);
            });

            if (Array.isArray(data.zones)) {
                data.zones.forEach((z) => {
                    const openEl = document.querySelector(`[data-zone-open="${z.id}"]`);
                    if (openEl) openEl.textContent = String(z.available_count);
                });
            }

            if (data.concierge) {
                const generalLink = document.getElementById("concierge-general-link");
                if (generalLink && data.concierge.general_deeplink) {
                    generalLink.href = data.concierge.general_deeplink;
                }
            }

            if (Array.isArray(data.tables)) {
                const byId = new Map(data.tables.map((t) => [String(t.id), t]));
                tableButtons.forEach((btn) => {
                    const t = byId.get(btn.dataset.tableId);
                    if (!t) return;

                    STATUS_CLASSES.forEach((cls) => btn.classList.remove(cls));
                    btn.classList.add(`status-${t.status}`);

                    btn.dataset.statusCode = t.status;
                    btn.dataset.status = t.status_display;
                    btn.dataset.perks = t.perks_text;
                    btn.dataset.notes = t.notes || "";
                    btn.dataset.deeplink = t.deeplink;
                    btn.dataset.capacityNum = String(t.capacity);
                    btn.dataset.capacity = `${t.capacity} pax`;
                    btn.dataset.minSpend = `₱${t.min_spend}`;

                    btn.setAttribute(
                        "aria-label",
                        `Table ${t.code}, ${t.zone_name}, ${t.capacity} guests, ${t.status_display}`
                    );
                    const metaMini = btn.querySelector(".table-meta-mini");
                    if (metaMini) {
                        metaMini.textContent = `${t.capacity}p • ${t.status_display}`;
                    }
                    if (dialog.open && activeDialogTableId === String(t.id)) {
                        populateDialog(btn);
                    }
                });
                applyFilters();
            }

            if (lastSyncedLabel) {
                const now = new Date();
                lastSyncedLabel.textContent = `Synced at ${now.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                })}`;
            }
        } catch (_err) {
            // Keep existing floor snapshot intact on transient network failure.
        }
    }

    if (refreshBtn) {
        refreshBtn.addEventListener("click", syncFloorStatus);
    }

    const POLL_INTERVAL_MS = 15000;
    window.setInterval(() => {
        if (!document.hidden) {
            syncFloorStatus();
        }
    }, POLL_INTERVAL_MS);

    // Safari / legacy fallback for <dialog closedby="any"> using pointerdown + pointerup
    // so a text-selection drag ending on the backdrop does not dismiss the dialog.
    if (!("closedBy" in HTMLDialogElement.prototype)) {
        const isOutside = (e, dlg) => {
            const r = dlg.getBoundingClientRect();
            return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
        };
        let pressedOutside = false;
        dialog.addEventListener("pointerdown", (e) => {
            pressedOutside = isOutside(e, dialog);
        });
        dialog.addEventListener("pointerup", (e) => {
            if (pressedOutside && isOutside(e, dialog)) {
                dialog.close();
            }
        });
    }
})();
