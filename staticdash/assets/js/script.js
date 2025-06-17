document.addEventListener("DOMContentLoaded", () => {
  const links = document.querySelectorAll(".nav-link");
  const sections = document.querySelectorAll(".page-section");

  function showPage(id) {
    sections.forEach(section => section.style.display = "none");
    const page = document.getElementById(id);
    if (page) page.style.display = "block";

    links.forEach(link => link.classList.remove("active"));
    const activeLink = Array.from(links).find(link => link.dataset.target === id);
    if (activeLink) activeLink.classList.add("active");
  }

  links.forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      const targetId = link.dataset.target;
      showPage(targetId);
    });
  });

  // Show the first page by default
  if (sections.length > 0) {
    showPage(sections[0].id);
  }
});
