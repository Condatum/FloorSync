document.addEventListener("DOMContentLoaded", () => {
    const darkModeField = document.querySelector("#id_dark_mode");
    const colorSchemeMeta = document.querySelector('meta[name="color-scheme"]');
    if (darkModeField) {
        const applyTheme = () => {
            const scheme = darkModeField.checked ? "dark" : "light";
            document.documentElement.dataset.theme = scheme;
            if (colorSchemeMeta) {
                colorSchemeMeta.setAttribute("content", scheme);
            }
        };
        darkModeField.addEventListener("change", applyTheme);
    }
});
