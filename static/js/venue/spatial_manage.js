(function () {
    const canvas = document.getElementById("spatial-preview-canvas");
    const marker = document.getElementById("spatial-active-marker");
    if (!canvas || !marker) return;

    const canvasW = parseFloat(canvas.dataset.canvasWidth || "1200");
    const canvasH = parseFloat(canvas.dataset.canvasHeight || "800");

    const posXInput = document.getElementById("id_pos_x");
    const posYInput = document.getElementById("id_pos_y");
    const widthInput = document.getElementById("id_width");
    const heightInput = document.getElementById("id_height");
    const rotationInput = document.getElementById("id_rotation");
    const shapeInput = document.getElementById("id_shape");
    const codeInput = document.getElementById("id_code");
    const coordsReadout = document.getElementById("spatial-coords-readout");
    const announcer = document.getElementById("spatial-drag-announcer");

    if (!posXInput || !posYInput || !widthInput || !heightInput) return;

    // Reveal interactive handle only after JS initializes (progressive enhancement).
    marker.hidden = false;

    let announceTimer = null;
    function announceMove(directionText) {
        if (!announcer) return;
        announcer.textContent = directionText;
        if (announceTimer) window.clearTimeout(announceTimer);
        announceTimer = window.setTimeout(() => {
            announcer.textContent = "";
        }, 1200);
    }

    function numVal(input, fallback) {
        const parsed = parseFloat(input.value);
        return Number.isFinite(parsed) ? parsed : fallback;
    }

    function clampCoords(x, y) {
        const w = Math.max(30, Math.min(canvasW, numVal(widthInput, 100)));
        const h = Math.max(30, Math.min(canvasH, numVal(heightInput, 70)));
        const clampedX = Math.round(Math.max(0, Math.min(x, canvasW - w)));
        const clampedY = Math.round(Math.max(0, Math.min(y, canvasH - h)));
        return { x: clampedX, y: clampedY, w, h };
    }

    function syncMarkerFromInputs() {
        const { x, y, w, h } = clampCoords(numVal(posXInput, 120), numVal(posYInput, 120));
        const rot = rotationInput ? numVal(rotationInput, 0) : 0;
        const shape = shapeInput ? shapeInput.value : "RECT";
        const code = (codeInput && codeInput.value.trim()) || "NEW";

        marker.style.left = `${(x / canvasW) * 100}%`;
        marker.style.top = `${(y / canvasH) * 100}%`;
        marker.style.width = `${(w / canvasW) * 100}%`;
        marker.style.height = `${(h / canvasH) * 100}%`;
        marker.style.setProperty("--table-rot", `${rot}deg`);

        marker.classList.remove("shape-RECT", "shape-CIRCLE", "shape-BOOTH");
        marker.classList.add(`shape-${shape}`);

        const labelEl = marker.querySelector("[data-marker-code]");
        if (labelEl) labelEl.textContent = code;
        if (coordsReadout) {
            coordsReadout.textContent = `Active placement: (${x}, ${y}) • ${w}×${h} • ${rot}°`;
        }
    }

    function applyPosition(nextX, nextY) {
        const { x, y } = clampCoords(nextX, nextY);
        posXInput.value = String(x);
        posYInput.value = String(y);
        syncMarkerFromInputs();
    }

    // Bidirectional sync when Super Admin edits form numbers directly.
    [posXInput, posYInput, widthInput, heightInput, rotationInput, shapeInput, codeInput].forEach((el) => {
        if (el) el.addEventListener("input", syncMarkerFromInputs);
        if (el) el.addEventListener("change", syncMarkerFromInputs);
    });

    // Single-pointer click-to-position on the floor canvas background (accessible non-drag alternative).
    canvas.addEventListener("click", (event) => {
        if (event.target.closest("a, button")) return;
        const rect = canvas.getBoundingClientRect();
        const w = numVal(widthInput, 100);
        const h = numVal(heightInput, 70);
        const rawX = ((event.clientX - rect.left) / rect.width) * canvasW - w / 2;
        const rawY = ((event.clientY - rect.top) / rect.height) * canvasH - h / 2;
        applyPosition(rawX, rawY);
        announceMove("Active table placement moved on floor canvas");
    });

    // Pointer capture dragging on the active table marker handle.
    let dragOffsetX = 0;
    let dragOffsetY = 0;

    marker.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) return;
        const canvasRect = canvas.getBoundingClientRect();
        const currentX = numVal(posXInput, 120);
        const currentY = numVal(posYInput, 120);
        const pointerCanvasX = ((event.clientX - canvasRect.left) / canvasRect.width) * canvasW;
        const pointerCanvasY = ((event.clientY - canvasRect.top) / canvasRect.height) * canvasH;
        dragOffsetX = pointerCanvasX - currentX;
        dragOffsetY = pointerCanvasY - currentY;
        marker.setPointerCapture(event.pointerId);
        marker.classList.add("dragging");
    });

    marker.addEventListener("pointermove", (event) => {
        if (!marker.hasPointerCapture(event.pointerId)) return;
        const canvasRect = canvas.getBoundingClientRect();
        const pointerCanvasX = ((event.clientX - canvasRect.left) / canvasRect.width) * canvasW;
        const pointerCanvasY = ((event.clientY - canvasRect.top) / canvasRect.height) * canvasH;
        applyPosition(pointerCanvasX - dragOffsetX, pointerCanvasY - dragOffsetY);
    });

    marker.addEventListener("lostpointercapture", () => {
        marker.classList.remove("dragging");
    });

    // Keyboard movement via arrow keys (15px default, 5px with Shift).
    marker.addEventListener("keydown", (event) => {
        const step = event.shiftKey ? 5 : 15;
        const currentX = numVal(posXInput, 120);
        const currentY = numVal(posYInput, 120);
        let dx = 0;
        let dy = 0;
        let dirLabel = "";

        if (event.key === "ArrowLeft") {
            dx = -step;
            dirLabel = "Table moved left";
        } else if (event.key === "ArrowRight") {
            dx = step;
            dirLabel = "Table moved right";
        } else if (event.key === "ArrowUp") {
            dy = -step;
            dirLabel = "Table moved up";
        } else if (event.key === "ArrowDown") {
            dy = step;
            dirLabel = "Table moved down";
        } else {
            return;
        }

        event.preventDefault();
        applyPosition(currentX + dx, currentY + dy);
        announceMove(dirLabel);
    });

    // Initialize default placement for new tables if pos_x/pos_y are empty.
    if (!posXInput.value) posXInput.value = "120";
    if (!posYInput.value) posYInput.value = "120";
    syncMarkerFromInputs();
})();
