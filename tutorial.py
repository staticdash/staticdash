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

# --- 4. Headers & Text with Markdown ---
page_headers = Page("headers", "Headers & Text with Markdown")
page_headers.add_text("""
You can add headers of different levels and paragraphs of text to organize your dashboard.

**Text supports full Markdown formatting:**
- **Bold text** with `**text**`
- *Italic text* with `*text*`
- ~~Strikethrough~~ with `~~text~~`
- `Inline code` with backticks

You can also create lists:
1. First item
2. Second item
3. Third item

And include [links](https://github.com/staticdash/staticdash) to external resources.
""")

page_headers.add_syntax(
    '''page.add_header("Header Level 2", level=2)
page.add_header("Header Level 3", level=3)
page.add_text("Text with **markdown** formatting!")''',
    language="python"
)
page_headers.add_header("Header Level 2", level=2)
page_headers.add_header("Header Level 3", level=3)
page_headers.add_header("Header Level 4", level=4)
page_headers.add_text("""
Headers help organize your dashboard and provide structure.

> Blockquotes are supported too!
> Great for highlighting important information.
""")
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
# Provide an explicit pixel height/width so the Plotly container renders correctly
page_plot.add_plot(fig_plotly, height=400, width=700)

x = np.linspace(0, 10, 100)
y = np.sin(x)
fig_matplotlib, ax = plt.subplots()
ax.plot(x, y, label="Sine Wave")
ax.set_title("Matplotlib: Sine Wave")
ax.set_xlabel("X-axis")
ax.set_ylabel("Y-axis")
ax.legend()
# Matplotlib static image with explicit pixel size
page_plot.add_plot(fig_matplotlib, height=300, width=600)

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

# --- 8. MathJax / LaTeX Math Demo ---
page_math = Page("math", "MathJax & Math Expressions")
page_math.add_text("""
StaticDash supports LaTeX math via MathJax. You can use inline math like $x^2 + y^2 = z^2$ 
or display math:

$$
E = mc^2
$$

More complex expressions work too:

$$
\\frac{\\partial f}{\\partial x} = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}
$$

Math expressions are preserved even when using markdown formatting like **bold** text.
""")
dashboard.add_page(page_math)

# --- 9. Mermaid Diagrams ---
page_mermaid = Page("diagrams", "Mermaid Diagrams")
page_mermaid.add_text("""
StaticDash supports Mermaid diagrams for visualizing workflows, architectures, and more!

**Flowchart Example:**

```mermaid
graph TD
    A[Data Collection] --> B{Data Valid?}
    B -->|Yes| C[Process Data]
    B -->|No| D[Log Error]
    C --> E[Generate Dashboard]
    D --> F[Notify Admin]
    E --> G[Publish]
```

**Sequence Diagram:**

```mermaid
sequenceDiagram
    participant User
    participant StaticDash
    participant Browser
    User->>StaticDash: Create dashboard
    StaticDash->>StaticDash: Generate HTML
    StaticDash-->>User: Output files
    User->>Browser: Open index.html
    Browser-->>User: Display dashboard
```

**Simple State Diagram:**

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Review: Submit
    Review --> Approved: Accept
    Review --> Draft: Reject
    Approved --> Published: Publish
    Published --> [*]
```

These diagrams render automatically and work offline!
""")
dashboard.add_page(page_mermaid)

# --- Export ---
dashboard.publish(output_dir="tutorial_output")
# dashboard.publish_pdf(
#     output_path="dashboard_report.pdf",
#     include_title_page=True,
#     title_page_marking="Title Page - StaticDash Inc.",
#     author="Brian Day",
#     affiliation="StaticDash Inc."
# )

# --- Directory Example ---
# Demonstrates using the Directory class to aggregate multiple dashboards
from staticdash import Directory

# Create a second dashboard for the directory example
dashboard2 = Dashboard("Sales Analysis", marking="Q4 2024 - Internal")
sales_page = Page("overview", "Sales Overview")
sales_page.add_text("This dashboard contains sales analysis for Q4 2024.")
sales_page.add_header("Key Metrics", level=2)
sales_data = pd.DataFrame({
    "Region": ["North", "South", "East", "West"],
    "Revenue": [125000, 98000, 110000, 87000],
    "Growth": ["12%", "8%", "15%", "5%"]
})
sales_page.add_table(sales_data)
dashboard2.add_page(sales_page)

# Create a directory and add both dashboards
directory = Directory(title="My Dashboard Collection")
directory.add_dashboard(dashboard, slug="tutorial")
directory.add_dashboard(dashboard2, slug="sales")
directory.publish(output_dir="directory_out")
