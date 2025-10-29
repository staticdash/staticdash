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

## Examples

- **Tutorial:** [`tutorial.py`](./tutorial.py) - Comprehensive tutorial showing all features
- **Weekly Planner:** [`weekly_planner.py`](./weekly_planner.py) - Beautiful weekly calendar/planner generator

### Weekly Planner Example

Generate a professional weekly planner with correct dates for any year:

```python
from weekly_planner import generate_weekly_planner

# Generate planner for 2025
planner = generate_weekly_planner(year=2025, num_weeks=52)
planner.publish(output_dir="weekly_planner_output")
```

Features:
- 📅 One page per week with 7 day boxes (Monday-Sunday)
- 📝 Large weekly notes section
- 🎨 Beautiful gradient styling
- 🖨️ Print-friendly design
- ✅ Correct dates for any year

---

For more examples, see the example files in this repository.