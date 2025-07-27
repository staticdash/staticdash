from staticdash import Page, Dashboard
from staticdash.dashboard import MiniPage
import plotly.express as px
import pandas as pd
import numpy as np

# --- 1. Create a Dashboard ---
dashboard = Dashboard("Staticdash Tutorial", page_width=900)

# --- 2. Introduction Page ---
page_intro = Page("intro", "Intro", page_width=800)
page_intro.add_text(
    "StaticDash is a Python library for building beautiful, interactive, static dashboards—no server required. "
    "You can combine plots, tables, code, downloads, and more, all with a simple API. "
    "This tutorial walks you through every feature with matching code and rendered output."
)
page_intro.add_syntax(
    '''from staticdash.dashboard import Dashboard, Page
dashboard = Dashboard(title="My Dashboard")''',
    language="python"
)
dashboard.add_page(page_intro)

# --- 3. Adding Pages to the Dashboard ---
page_add = Page("add-pages", "Adding Pages")
page_add.add_text(
    "A dashboard is made up of one or more **pages**. Each page gets a title, a unique slug, and any content you want. "
    "To add a page, create a `Page` object and use `dashboard.add_page(page)`."
)
page_add.add_syntax(
    '''page = Page("overview", "Overview")
dashboard.add_page(page)''',
    language="python"
)
dashboard.add_page(page_add)

# --- 4. Headers & Text ---
page_headers = Page("headers", "Headers & Text")
page_headers.add_text(
    "You can add headers of different levels and paragraphs of text to organize your dashboard."
)
page_headers.add_syntax(
    '''page.add_header("Header Level 2", level=2)
page.add_header("Header Level 3", level=3)
page.add_header("Header Level 4", level=4)
page.add_text("This is a paragraph of text.")''',
    language="python"
)
page_headers.add_header("Header Level 2", level=2)
page_headers.add_header("Header Level 3", level=3)
page_headers.add_header("Header Level 4", level=4)
page_headers.add_text("This is a paragraph of text. Headers help organize your dashboard and provide structure.")
dashboard.add_page(page_headers)

# --- 5. Plotly Figures ---
df = px.data.gapminder().query("year == 2007")
fig = px.scatter(df, x="gdpPercap", y="lifeExp", size="pop", color="continent",
                 hover_name="country", log_x=True, size_max=60, title="GDP vs Life Expectancy (2007)")

page_plot = Page("plots", "Plotly Figures")
page_plot.add_text(
    "Add interactive Plotly figures to your dashboard. Just pass a Plotly figure to `add_plot`."
)
page_plot.add_syntax(
    '''import plotly.express as px
df = px.data.gapminder().query("year == 2007")
fig = px.scatter(df, x="gdpPercap", y="lifeExp", size="pop", color="continent",
                 hover_name="country", log_x=True, size_max=60)
page.add_plot(fig)''',
    language="python"
)
page_plot.add_plot(fig)
dashboard.add_page(page_plot)

# --- 6. Tables ---
df2 = df[["country", "continent", "lifeExp", "gdpPercap"]].sort_values("lifeExp", ascending=False).head(10)

page_table = Page("tables", "Tables")
page_table.add_text(
    "Add pandas DataFrames as sortable, styled tables. Just use `add_table(df)`."
)
page_table.add_syntax(
    '''df2 = df[["country", "continent", "lifeExp", "gdpPercap"]]
df2 = df2.sort_values("lifeExp", ascending=False).head(10)
page.add_table(df2)''',
    language="python"
)
page_table.add_table(df2)
dashboard.add_page(page_table)

# --- 7. Download Buttons ---
with open("tutorial_sample.txt", "w") as f:
    f.write("This is a sample file for download.")

page_download = Page("downloads", "Download Buttons")
page_download.add_text(
    "Add download buttons for any file. Users can download results, data, or code."
)
page_download.add_syntax(
    '''with open("tutorial_sample.txt", "w") as f:
    f.write("This is a sample file for download.")
page.add_download("./tutorial_sample.txt", "Download Sample File")''',
    language="python"
)
page_download.add_download("./tutorial_sample.txt", "Download Sample File")
dashboard.add_page(page_download)

# --- 8. MiniPages (Horizontal Rows) ---
fig1 = px.histogram(df, x="lifeExp", nbins=20, title="Life Expectancy Histogram")
fig2 = px.box(df, x="continent", y="gdpPercap", log_y=True, title="GDP per Capita by Continent")

page_minipage = Page("minipage", "MiniPages (Horizontal Rows)")
page_minipage.add_text(
    "Use MiniPages to arrange multiple elements side by side (in a horizontal row)."
)
page_minipage.add_syntax(
    '''fig1 = px.histogram(df, x="lifeExp", nbins=20)
fig2 = px.box(df, x="continent", y="gdpPercap", log_y=True)
mini = MiniPage()
mini.add_plot(fig1)
mini.add_plot(fig2)
page.add_minipage(mini)''',
    language="python"
)
mini = MiniPage()
mini.add_plot(fig1)
mini.add_plot(fig2)
page_minipage.add_minipage(mini)
dashboard.add_page(page_minipage)

# --- 9. MiniPages: Mixed Content ---
mini2a = MiniPage()
mini2a.add_text("Box plot shows GDP per capita by continent.")
mini2a.add_plot(fig2)

mini2b = MiniPage()
mini2b.add_table(df2.head(3))
mini2b.add_syntax('print("MiniPage with a table and code")', language="python")

page_minipage2 = Page("minipage2", "MiniPages: Mixed Content")
page_minipage2.add_text(
    "MiniPages can mix text, plots, tables, and code side by side. Here are two examples:"
)
page_minipage2.add_syntax(
    '''mini1 = MiniPage()
mini1.add_text("Box plot shows GDP per capita by continent.")
mini1.add_plot(fig2)

mini2 = MiniPage()
mini2.add_table(df2.head(3))
mini2.add_syntax('print("MiniPage with a table and code")', language="python")

page.add_minipage(mini1)
page.add_minipage(mini2)''',
    language="python"
)
page_minipage2.add_minipage(mini2a)
page_minipage2.add_minipage(mini2b)
dashboard.add_page(page_minipage2)

# --- 10. Syntax Highlighted Code Blocks ---
page_code = Page("syntax", "Syntax Highlighted Code")
page_code.add_text(
    "Show code in any language with syntax highlighting, copy, and view-raw buttons. "
    "A header above each block shows the language."
)

code_snippets = [
    ("python", '''def greet(name):\n    return f"Hello, {name}"'''),
    ("javascript", '''console.log("Hello, world!");'''),
    ("sql", '''SELECT * FROM users WHERE active = 1;'''),
    ("markup", '''<div>Hello</div>'''),
    ("bash", '''echo "Deploy complete."'''),
    ("json", '''{\n  "key": "value",\n  "count": 42\n}'''),
    ("c", '''#include <stdio.h>\nint main() { printf("Hi"); return 0; }''')
]

for lang, code in code_snippets:
    page_code.add_header(f"{lang.capitalize()} Example", level=3)
    page_code.add_syntax(code, language=lang)

dashboard.add_page(page_code)

# --- 11. Combining Everything ---
mini_combo = MiniPage()
mini_combo.add_plot(fig1)
mini_combo.add_table(df2.head(5))
mini_combo.add_syntax("print('Hello from MiniPage')", language="python")

page_combo = Page("combo", "Combining Features")
page_combo.add_text(
    "You can mix all features—plots, tables, code, downloads, and MiniPages—on a single page."
)
page_combo.add_syntax(
    '''mini = MiniPage()
mini.add_plot(fig1)
mini.add_table(df2.head(5))
mini.add_syntax("print('Hello from MiniPage')", language="python")
page.add_minipage(mini)
page.add_table(df2)''',
    language="python"
)
page_combo.add_minipage(mini_combo)
page_combo.add_table(df2)
dashboard.add_page(page_combo)

# --- 12. Exporting the Dashboard ---
page_export = Page("export", "Export HTML")
page_export.add_text(
    "When you're ready, export your dashboard to static HTML files. "
    "This generates an `index.html` (multi-page app) and a separate HTML file for each page."
)
page_export.add_syntax(
    '''dashboard.publish(output_dir="tutorial_output")''',
    language="python"
)
dashboard.add_page(page_export)

# --- Main Page ---
main = Page("main", "Main Page")
main.add_text("This is the main page.")

# --- Subpage 1 ---
sub1 = Page("sub1", "Subpage 1")
sub1.add_text("This is subpage 1.")

# --- Subpage 2 ---
sub2 = Page("sub2", "Subpage 2")
sub2.add_text("This is subpage 2.")

# --- About Page ---
about = Page("about", "About")
about.add_text("This is an About page.")

# --- Organize Pages ---
main.add_subpage(sub1)
main.add_subpage(sub2)

dashboard.add_page(main)
dashboard.add_page(about)

# --- Export ---
dashboard.publish(output_dir="tutorial_output")
dashboard.publish_pdf(
    output_path="dashboard_report.pdf",
    include_title_page=True,
    author="Brian Day",
    affiliation="StaticDash Inc."
)