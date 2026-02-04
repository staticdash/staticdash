# staticdash

<p align="center">
  <img src="https://raw.githubusercontent.com/staticdash/staticdash/main/logo.svg" alt="staticdash logo" width="220" height="50">
</p>

staticdash is a lightweight Python module for creating static, multi-page HTML dashboards. It supports:

- **Plotly plots:** Interactive, responsive visualizations
- **Matplotlib figures:** Static plots and charts
- **Pandas DataFrames:** Sortable, searchable tables
- **Rich text formatting:** Full Markdown support including **bold**, *italic*, ~~strikethrough~~, lists, links, tables, and blockquotes
- **Math expressions:** LaTeX math rendering with MathJax (inline `$...$` and display `$$...$$`)
- **Mermaid diagrams:** Flowcharts, sequence diagrams, state diagrams, and more
- **File downloads:** Add download buttons for any file
- **Multi-page navigation:** Hierarchical sidebar with subpages
- **Custom styling:** Easily customize CSS and JavaScript
- **Air-gapped support:** All assets vendored for offline environments

## Installation

```bash
pip install staticdash 
```

## Features

### Content Types

- **Add Plotly figures:** `page.add(fig)` - Interactive plots with zoom, pan, hover tooltips
- **Add Matplotlib figures:** `page.add(fig)` - Static plots converted to PNG
- **Add tables:** `page.add(df)` - Pandas DataFrames rendered as sortable, searchable tables
- **Add text:** `page.add("Your text")` - Full Markdown support including:
  - **Bold**, *italic*, ~~strikethrough~~
  - Lists (ordered and unordered)
  - Links, blockquotes, code blocks
  - Tables in Markdown syntax
- **Add headers:** `page.add_header("Title", level=2)` - Markdown headers (h1-h6)
- **Add math:** Use `$inline math$` or `$$display math$$` for LaTeX expressions
- **Add diagrams:** Use ` ```mermaid ` code blocks for flowcharts, sequence diagrams, state diagrams, gantt charts
- **Add downloads:** `page.add_download("path/to/file", "Label")` - File download buttons

### Layout & Styling

- **Sidebar navigation:** Fixed sidebar with hierarchical pages and subpages
- **Responsive design:** Works on desktop and mobile devices
- **Custom styling:** Edit `assets/css/style.css` for your own look
- **Per-page HTML:** Individual HTML files for each page plus combined dashboard

### Air-Gapped Support

All external dependencies (Plotly, MathJax, Mermaid, Prism) are vendored during installation, ensuring dashboards work completely offline without internet access or CDN dependencies.

## Live Demos

- **[Tutorial Dashboard](https://staticdash.github.io/staticdash/tutorial_output/)** - Comprehensive feature demonstration
- **[Directory Example](https://staticdash.github.io/staticdash/directory_out/)** - Multiple dashboard aggregation

## Examples

The repository includes a comprehensive tutorial demonstrating all features:

**Tutorial Dashboard:** Run `python tutorial.py` to generate `tutorial_output/index.html`

The tutorial demonstrates:
- Basic page creation and navigation
- Text formatting with Markdown (bold, italic, strikethrough, lists, links, tables)
- Plotly and Matplotlib figures
- Pandas DataFrame tables
- Subpages and hierarchical navigation
- MathJax math expressions (inline and display)
- Mermaid diagrams (flowcharts, sequence diagrams, state diagrams)
- Directory class for aggregating multiple dashboards

---

For the source code, see [`tutorial.py`](./tutorial.py) in this repository.