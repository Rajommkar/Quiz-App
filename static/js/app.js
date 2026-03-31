document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".alert").forEach((alert) => {
        setTimeout(() => {
            const closeBtn = alert.querySelector(".btn-close");
            if (closeBtn) closeBtn.click();
        }, 3500);
    });
});
