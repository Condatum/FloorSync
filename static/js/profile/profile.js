document.addEventListener("DOMContentLoaded", () => {
    const bioField = document.querySelector("#id_bio");
    if (bioField) {
        bioField.setAttribute("maxlength", "500");
    }
});
