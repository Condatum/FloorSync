document.addEventListener("DOMContentLoaded", () => {
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

    const password1 = document.querySelector("#id_password1");
    const password2 = document.querySelector("#id_password2");
    if (!password1 || !password2) {
        return;
    }

    const supportsUserInvalid = CSS.supports("selector(:user-invalid)");
    const syncValidity = (input) => {
        const isValid = input.validity.valid;
        input.setAttribute("aria-invalid", isValid ? "false" : "true");
        if (!supportsUserInvalid) {
            input.classList.toggle("user-invalid-fallback", !isValid);
            input.classList.toggle("user-valid-fallback", isValid);
        }
    };

    const checkMatch = () => {
        if (password2.value.length > 0 && password1.value !== password2.value) {
            password2.setCustomValidity("Passwords do not match.");
        } else {
            password2.setCustomValidity("");
        }
    };

    password2.addEventListener("blur", () => {
        checkMatch();
        syncValidity(password2);
    });

    password2.addEventListener("input", () => {
        password2.setCustomValidity("");
        if (password2.getAttribute("aria-invalid") === "true") {
            checkMatch();
            syncValidity(password2);
        }
    });

    password1.addEventListener("input", () => {
        if (password2.value.length > 0) {
            checkMatch();
            if (password2.getAttribute("aria-invalid") === "true") {
                syncValidity(password2);
            }
        }
    });
});
