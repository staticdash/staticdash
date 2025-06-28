# staticdash

<p align="center">
  <img src="https://raw.githubusercontent.com/staticdash/staticdash/main/logo.svg" alt="staticdash logo" width="220" height="50">
</p>

staticdash is a lightweight Python module for creating static, multi-page HTML dashboards. It supports:

- Plotly plots (interactive, responsive)
- Pandas DataFrames as sortable tables
- Text and headers (Markdown-like)
- File download buttons
- Multi-page navigation with sidebar
- Custom CSS and JavaScript
- Easy extension for new content types

## Installation

```bash
pip install staticdash 
```

## Features

- **Add Plotly figures:** `page.add(fig)`
- **Add tables:** `page.add(df)` (sortable by default)
- **Add text or headers:** `page.add("Some text")`, `page.add_header("Title", level=2)`
- **Add download buttons:** `page.add_download("path/to/file", "Label")`
- **Multi-page:** Create multiple `Page` objects and add them to your `Dashboard`
- **Custom styling:** Edit `assets/css/style.css` for your own look

## Options

- **Sidebar navigation:** Fixed, with active highlighting
- **Responsive layout:** Works on desktop and mobile
- **Export:** Outputs a static HTML dashboard (no server needed)
- **Per-page HTML:** Also generates individual HTML files for each page

## Live Demo

[View the latest demo dashboard](https://staticdash.github.io/staticdash/)

---

For a full example, see [`demo.py`](./demo.py) in this repository.