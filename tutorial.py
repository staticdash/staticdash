from staticdash import Page, Dashboard
from staticdash.dashboard import MiniPage
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- 1. Create a Dashboard ---
dashboard = Dashboard(
    "Staticdash Tutorial",
    marking="Confidential - For Internal Use Only",
    distribution="DISTRIBUTION STATEMENT A. Approved for public release."
)

# --- 2. Introduction Page ---
page_intro = Page("intro", "Introduction", marking="Public - Not Confidential")
page_intro.add_text(
    "StaticDash is a Python library for building beautiful, interactive, static dashboards—no server required. "
    "You can combine plots, tables, code, downloads, and more, all with a simple API."
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

# --- 5. Plotly and Matplotlib Figures ---
page_plot = Page("plots", "Plotly and Matplotlib Figures", marking="Figures - Confidential")
page_plot.add_text(
    "Add interactive Plotly figures to your dashboard. Just pass a Plotly figure to `add_plot`."
)
df = px.data.gapminder().query("year == 2007")
fig_plotly = px.scatter(
    df, x="gdpPercap", y="lifeExp", size="pop", color="continent",
    hover_name="country", log_x=True, size_max=60, title="Plotly: GDP vs Life Expectancy (2007)"
)
page_plot.add_plot(fig_plotly)

x = np.linspace(0, 10, 100)
y = np.sin(x)
fig_matplotlib, ax = plt.subplots()
ax.plot(x, y, label="Sine Wave")
ax.set_title("Matplotlib: Sine Wave")
ax.set_xlabel("X-axis")
ax.set_ylabel("Y-axis")
ax.legend()
page_plot.add_plot(fig_matplotlib)

dashboard.add_page(page_plot)

# --- 6. Tables ---
df2 = df[["country", "continent", "lifeExp", "gdpPercap"]].sort_values("lifeExp", ascending=False).head(10)
page_table = Page("tables", "Tables")
page_table.add_text(
    "Add pandas DataFrames as sortable, styled tables. Just use `add_table(df)`."
)
page_table.add_table(df2)
dashboard.add_page(page_table)

# --- 7. Main Page with Subpages ---
main = Page("main", "Main Page", marking="Main Page - Internal Use Only")
main.add_text("This is the main page.")

sub1 = Page("sub1", "Subpage 1", marking="Subpage 1 - Restricted")
sub1.add_text("This is subpage 1.")

sub2 = Page("sub2", "Subpage 2")
sub2.add_text("This is subpage 2.")

main.add_subpage(sub1)
main.add_subpage(sub2)

dashboard.add_page(main)

# --- Export ---
dashboard.publish(output_dir="tutorial_output")
dashboard.publish_pdf(
    output_path="dashboard_report.pdf",
    include_title_page=True,
    title_page_marking="Title Page - StaticDash Inc.",
    author="Brian Day",
    affiliation="StaticDash Inc."
)
