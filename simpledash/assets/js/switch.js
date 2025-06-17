document.addEventListener("DOMContentLoaded", function () {
    const links = document.querySelectorAll(".nav-link");
    const pages = document.querySelectorAll(".page-section");

    function showPage(id) {
        pages.forEach(p => p.classList.remove("active"));
        document.getElementById(id).classList.add("active");
    }

    links.forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const pageId = this.getAttribute("data-page");
            showPage(pageId);
        });
    });

    if (pages.length > 0) {
        pages[0].classList.add("active");
    }
});