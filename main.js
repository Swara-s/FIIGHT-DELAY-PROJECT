document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("predictionForm");
    const loader = document.getElementById("loader");

    if (form && loader) {
        form.addEventListener("submit", () => {
            loader.classList.remove("d-none");
        });
    }
});
