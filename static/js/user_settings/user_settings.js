document.addEventListener("DOMContentLoaded", () => {
    const darkModeField = document.querySelector("#id_dark_mode");
    if (darkModeField) {
        const applyTheme = () => {
            document.documentElement.dataset.theme = darkModeField.checked ? "dark" : "light";
        };
        darkModeField.addEventListener("change", applyTheme);
    }
});
