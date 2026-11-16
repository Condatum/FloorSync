document.addEventListener("DOMContentLoaded", () => {
    const usernameField = document.querySelector("#id_username");
    if (usernameField) {
        usernameField.focus();
    }

    document.querySelectorAll(".btn-toggle-password").forEach((button) => {
        button.addEventListener("click", () => {
            const targetId = button.getAttribute("aria-controls");
            const input = targetId ? document.getElementById(targetId) : null;
            if (!input) return;
            const show = input.type === "password";
            input.type = show ? "text" : "password";
            button.setAttribute("aria-pressed", show ? "true" : "false");
            button.textContent = show ? "Hide" : "Show";
        });
    });
});
