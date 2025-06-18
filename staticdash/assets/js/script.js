document.addEventListener("DOMContentLoaded", () => {
  const links = document.querySelectorAll(".nav-link");
  const sections = document.querySelectorAll(".page-section");

  function resizePlotsIn(section) {
    const plots = section.querySelectorAll(".plotly-graph-div");
    plots.forEach(plot => {
      if (typeof Plotly !== "undefined" && plot.data) {
        Plotly.Plots.resize(plot);
      }
    });
  }

  function showPage(id) {
    sections.forEach(section => section.style.display = "none");
    const page = document.getElementById(id);
    if (page) {
      page.style.display = "block";

      // Resize Plotly charts within the newly visible section
      requestAnimationFrame(() => {
        resizePlotsIn(page);
      });
    }

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

  // Initial page load
  if (sections.length > 0) {
    showPage(sections[0].id);
  }
});