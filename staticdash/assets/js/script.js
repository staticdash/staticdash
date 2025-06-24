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

  function showPage(pageId) {
    sections.forEach(section => section.style.display = "none");
    const page = document.getElementById(pageId);
    if (page) {
      page.style.display = "block";

      // Resize Plotly charts within the newly visible section
      requestAnimationFrame(() => {
        resizePlotsIn(page);
      });
    }

    links.forEach(link => link.classList.remove("active"));
    const activeLink = Array.from(links).find(link => link.dataset.target === pageId);
    if (activeLink) activeLink.classList.add("active");

    if (window.Prism && typeof Prism.highlightAll === "function") {
      Prism.highlightAll();
    }
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

  // Table sorting for tables with class "sortable"
  document.querySelectorAll("table.sortable").forEach(function (table) {
    const headers = table.querySelectorAll("thead th");
    let originalRows = null;

    headers.forEach(function (th, colIdx) {
      th.addEventListener("click", function () {
        if (!originalRows) {
          const tbody = table.querySelector("tbody");
          originalRows = Array.from(tbody.querySelectorAll("tr"));
        }

        // Cycle: none -> asc -> desc -> none
        let state = th.dataset.sorted;
        let nextState = state === "asc" ? "desc" : state === "desc" ? "none" : "asc";

        headers.forEach(h => {
          h.classList.remove("sorted-asc", "sorted-desc");
          h.dataset.sorted = "none";
        });

        th.dataset.sorted = nextState;
        if (nextState === "asc") th.classList.add("sorted-asc");
        if (nextState === "desc") th.classList.add("sorted-desc");

        const tbody = table.querySelector("tbody");
        if (nextState === "none") {
          originalRows.forEach(row => tbody.appendChild(row));
          return;
        }

        const rows = Array.from(tbody.querySelectorAll("tr"));
        rows.sort(function (a, b) {
          const aText = a.children[colIdx].textContent.trim();
          const bText = b.children[colIdx].textContent.trim();
          // Numeric sort if both are numbers
          const aNum = parseFloat(aText);
          const bNum = parseFloat(bText);
          if (!isNaN(aNum) && !isNaN(bNum)) {
            return nextState === "asc" ? aNum - bNum : bNum - aNum;
          }
          // String sort (works for ISO dates)
          return nextState === "asc"
            ? aText.localeCompare(bText)
            : bText.localeCompare(aText);
        });
        rows.forEach(row => tbody.appendChild(row));
      });
    });
  });

  // Syntax block copy/view raw
  document.querySelectorAll(".copy-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.preventDefault();
      const codeId = btn.dataset.target;
      const code = document.getElementById(codeId);
      if (code) {
        navigator.clipboard.writeText(code.textContent);
        btn.textContent = "Copied!";
        setTimeout(() => { btn.textContent = "Copy"; }, 1200);
      }
    });
  });
  document.querySelectorAll(".view-raw-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      e.preventDefault();
      const codeId = btn.dataset.target;
      const code = document.getElementById(codeId);
      if (code) {
        const win = window.open("", "_blank");
        win.document.write("<pre>" + code.textContent.replace(/[<>&]/g, c => ({
          '<': '&lt;', '>': '&gt;', '&': '&amp;'
        }[c])) + "</pre>");
        win.document.close();
      }
    });
  });
});