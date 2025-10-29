document.addEventListener("DOMContentLoaded", () => {
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

  // --- Sidebar dropdowns (remember open state) ---
  // Helper: get unique slug for each group from the link's href
  function getGroupSlug(group) {
    const link = group.querySelector('.sidebar-parent');
    return link ? link.getAttribute('href') : null;
  }

  function saveSidebarState() {
    const openGroups = Array.from(document.querySelectorAll('.sidebar-group.open'))
      .map(getGroupSlug)
      .filter(Boolean);
    localStorage.setItem("sidebar-open-groups", JSON.stringify(openGroups));
  }

  function restoreSidebarState() {
    const openGroups = JSON.parse(localStorage.getItem("sidebar-open-groups") || "[]");
    document.querySelectorAll('.sidebar-group').forEach(group => {
      const slug = getGroupSlug(group);
      if (slug && openGroups.includes(slug)) {
        group.classList.add('open');
      } else {
        group.classList.remove('open');
      }
    });
  }

  // Restore open groups from localStorage
  const openGroups = JSON.parse(localStorage.getItem("sidebar-open-groups") || "[]");
  document.querySelectorAll('.sidebar-group').forEach(group => {
    const slug = getGroupSlug(group);
    if (slug && openGroups.includes(slug)) {
      group.classList.add('open');
    }
  });

  // Toggle open/closed and save state
  document.querySelectorAll('.sidebar-parent').forEach(parent => {
    parent.addEventListener('click', function(e) {
      if (e.target.classList.contains('sidebar-arrow')) {
        e.preventDefault();
        const group = parent.closest('.sidebar-group');
        if (group) {
          group.classList.toggle('open');
          saveSidebarState();
        }
      }
    });
  });

  // --- Sidebar scroll position persistence ---
  const sidebar = document.getElementById("sidebar");
  // Restore scroll position on load
  if (sidebar && localStorage.getItem("sidebar-scroll")) {
    sidebar.scrollTop = parseInt(localStorage.getItem("sidebar-scroll"), 10);
  }
  // Save scroll position before navigating away
  window.addEventListener("pagehide", () => {
    if (sidebar) {
      localStorage.setItem("sidebar-scroll", sidebar.scrollTop);
    }
  });

  // Enable sidebar transitions after initial render
  setTimeout(() => {
    document.body.classList.add("sidebar-animate");
  }, 0);

  // --- Sidebar collapse/expand memory ---
  function saveSidebarState() {
    const expanded = [];
    document.querySelectorAll('.sidebar-group .sidebar-children').forEach(el => {
      if (el.classList.contains('expanded')) {
        // Use parent page slug as key
        const parent = el.parentElement.querySelector('.sidebar-parent, .nav-link');
        if (parent && parent.getAttribute('href')) {
          expanded.push(parent.getAttribute('href'));
        }
      }
    });
    localStorage.setItem('sidebarExpanded', JSON.stringify(expanded));
  }

  function restoreSidebarState() {
    const expanded = JSON.parse(localStorage.getItem('sidebarExpanded') || '[]');
    document.querySelectorAll('.sidebar-group').forEach(group => {
      const parent = group.querySelector('.sidebar-parent, .nav-link');
      const children = group.querySelector('.sidebar-children');
      if (parent && children) {
        if (expanded.includes(parent.getAttribute('href'))) {
          children.classList.add('expanded');
        } else {
          children.classList.remove('expanded');
        }
      }
    });
  }

  restoreSidebarState();

  document.querySelectorAll('.sidebar-group .sidebar-parent, .sidebar-group .nav-link').forEach(parent => {
    parent.addEventListener('click', function(e) {
      // Only toggle if arrow or parent link is clicked
      if (e.target.classList.contains('sidebar-arrow') || e.currentTarget === e.target) {
        const group = parent.closest('.sidebar-group');
        const children = group.querySelector('.sidebar-children');
        if (children) {
          children.classList.toggle('expanded');
          saveSidebarState();
        }
      }
    });
  });
});

/* CSS */
/* Add this CSS to handle the rotation of the arrow icon */
body.sidebar-animate .sidebar-group.open .sidebar-arrow {
  transform: rotate(90deg);
}