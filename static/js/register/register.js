document.addEventListener("DOMContentLoaded", () => {
    const password1 = document.querySelector("#id_password1");
    const password2 = document.querySelector("#id_password2");
    const submitButton = document.querySelector("#btn-register");
    if (!password1 || !password2 || !submitButton) {
        return;
    }

    const checkMatch = () => {
        const mismatched = password2.value.length > 0 && password1.value !== password2.value;
        password2.style.borderColor = mismatched ? "#ef4444" : "";
    };

    password1.addEventListener("input", checkMatch);
    password2.addEventListener("input", checkMatch);
});
