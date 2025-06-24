from staticdash.dashboard import Dashboard, Page, MiniPage
import plotly.express as px
import pandas as pd
import numpy as np

dashboard = Dashboard(title="StaticDash")

# --- 1. Introduction ---
page_intro = Page("intro", "Welcome to StaticDash")
page_intro.add_syntax(
    '''dashboard = Dashboard(title="StaticDash")''',
    language="python"
)
page_intro.add_text(
    "StaticDash is a Python library for building beautiful, interactive, static dashboards with no server required. "
    "You can combine plots, tables, code, downloads, and more, all with a simple API. "
    "This tutorial walks you through every feature with matching code and rendered output."
)
dashboard.add_page(page_intro)

# --- 2. Headers & Text ---
page_headers = Page("headers", "Headers & Text")
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

# --- 3. Plotly Figures ---
df = px.data.gapminder().query("year == 2007")
fig = px.scatter(df, x="gdpPercap", y="lifeExp", size="pop", color="continent",
                 hover_name="country", log_x=True, size_max=60, title="GDP vs Life Expectancy (2007)")

page_plot = Page("plots", "Plotly Figures")
page_plot.add_syntax(
    '''df = px.data.gapminder().query("year == 2007")
fig = px.scatter(df, x="gdpPercap", y="lifeExp", size="pop", color="continent",
                 hover_name="country", log_x=True, size_max=60)
page.add_plot(fig)''',
    language="python"
)
page_plot.add_text("This scatter plot shows GDP vs Life Expectancy by country, with population as bubble size.")
page_plot.add_plot(fig)
dashboard.add_page(page_plot)

# --- 4. Tables ---
df2 = df[["country", "continent", "lifeExp", "gdpPercap"]].sort_values("lifeExp", ascending=False).head(10)

page_table = Page("tables", "Tables")
page_table.add_syntax(
    '''df2 = df[["country", "continent", "lifeExp", "gdpPercap"]]
df2 = df2.sort_values("lifeExp", ascending=False).head(10)
page.add_table(df2)''',
    language="python"
)
page_table.add_text("This table shows the top 10 countries by life expectancy in 2007.")
page_table.add_table(df2)
dashboard.add_page(page_table)

# --- 5. Download Buttons ---
with open("tutorial_sample.txt", "w") as f:
    f.write("This is a sample file for download.")

page_download = Page("downloads", "Download Buttons")
page_download.add_syntax(
    '''with open("tutorial_sample.txt", "w") as f:
    f.write("This is a sample file for download.")
page.add_download("./tutorial_sample.txt", "Download Sample File")''',
    language="python"
)
page_download.add_text("Download buttons let users save your outputs, results, or code.")
page_download.add_download("./tutorial_sample.txt", "Download Sample File")
dashboard.add_page(page_download)

# --- 6. MiniPages (Horizontal Rows) ---
fig1 = px.histogram(df, x="lifeExp", nbins=20, title="Life Expectancy Histogram")
fig2 = px.box(df, x="continent", y="gdpPercap", log_y=True, title="GDP per Capita by Continent")

page_minipage = Page("minipage", "MiniPages (Horizontal Rows)")
page_minipage.add_syntax(
    '''fig1 = px.histogram(df, x="lifeExp", nbins=20)
fig2 = px.box(df, x="continent", y="gdpPercap", log_y=True)
mini = MiniPage()
mini.add_plot(fig1)
mini.add_plot(fig2)
page.add_minipage(mini)''',
    language="python"
)
page_minipage.add_text("Use MiniPages to place multiple elements horizontally.")
mini = MiniPage()
mini.add_plot(fig1)
mini.add_plot(fig2)
page_minipage.add_minipage(mini)
dashboard.add_page(page_minipage)

# --- 7. MiniPages: Mixed Content ---
mini2 = MiniPage()
mini2.add_text("Box plot shows GDP per capita by continent.")
mini2.add_plot(fig2)
mini2.add_table(df2.head(3))

page_minipage2 = Page("minipage2", "MiniPages: Mixed Content")
page_minipage2.add_syntax(
    '''mini = MiniPage()
mini.add_text("Box plot shows GDP per capita by continent.")
mini.add_plot(fig2)
mini.add_table(df2.head(3))
page.add_minipage(mini)''',
    language="python"
)
page_minipage2.add_text("MiniPages can mix text, plots, and tables side by side.")
page_minipage2.add_minipage(mini2)
dashboard.add_page(page_minipage2)

# --- 8. Syntax Highlighted Code Blocks ---
page_code = Page("syntax", "Syntax Highlighted Code")
page_code.add_text("Code blocks can show multiple languages and support copy/view raw buttons.")

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
    page_code.add_syntax(code, language=lang)

dashboard.add_page(page_code)

# --- 9. Combining Everything ---
mini_combo = MiniPage()
mini_combo.add_plot(fig1)
mini_combo.add_table(df2.head(5))
mini_combo.add_syntax("print('Hello from MiniPage')", language="python")

page_combo = Page("combo", "Combining Features")
page_combo.add_syntax(
    '''mini = MiniPage()
mini.add_plot(fig1)
mini.add_table(df2.head(5))
mini.add_syntax("print('Hello from MiniPage')", language="python")
page.add_minipage(mini)
page.add_table(df2)''',
    language="python"
)
page_combo.add_text("MiniPages can mix all features. Standalone content can follow.")
page_combo.add_minipage(mini_combo)
page_combo.add_table(df2)
dashboard.add_page(page_combo)

# --- 10. Per-Page Export ---
page_export = Page("export", "Export HTML")
page_export.add_syntax(
    '''dashboard.publish(output_dir="tutorial_output")''',
    language="python"
)
page_export.add_text("Use `.publish()` to generate `index.html` and per-page HTML files.")
dashboard.add_page(page_export)

# --- Export ---
dashboard.publish(output_dir="tutorial_output")