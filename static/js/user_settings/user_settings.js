document.addEventListener("DOMContentLoaded", () => {
    const darkModeField = document.querySelector("#id_dark_mode");
    if (darkModeField) {
        darkModeField.addEventListener("change", () => {
            document.body.style.filter = darkModeField.checked ? "none" : "brightness(1.05)";
        });
    }
});
