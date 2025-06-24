from staticdash.dashboard import Dashboard, Page, MiniPage
import plotly.express as px
import pandas as pd
import numpy as np

# Create sample data
df = pd.DataFrame({
    "Category": ["A", "B", "C", "D"],
    "Value": [10, 20, 30, 40]
})

df2 = pd.DataFrame({
    "Time": pd.date_range("2024-01-01", periods=10, freq="D"),
    "Signal": np.random.randn(10).cumsum()
})

# Ensure Time column is string for sorting
df2["Time"] = df2["Time"].dt.strftime("%Y-%m-%d %H:%M:%S")

fig1 = px.bar(df, x="Category", y="Value", title="Bar Chart Example")
fig2 = px.line(df2, x="Time", y="Signal", title="Signal over Time")

# Build dashboard
dashboard = Dashboard(title="StaticDash Demo")

# Page 1: Overview
page1 = Page("overview", "Overview")
page1.add_header("Section 1: Introduction", level=2)
page1.add_text("Welcome to the StaticDash demo. Below is a bar chart and a table.")
page1.add_plot(fig1)
page1.add_table(df)
page1.add_syntax(
    "import numpy as np\nprint(np.arange(10))",
    language="python"
)
page1.add_syntax(
    "console.log('Hello, world!');",
    language="javascript"
)

# Page 2: Timeseries
page2 = Page("timeseries", "Timeseries")
page2.add_header("Random Time Series", level=2)
page2.add_text("Here is a random time series with cumulative noise.")
page2.add_plot(fig2)
page2.add_table(df2)

# Page 3: Summary
page3 = Page("summary", "Summary")
page3.add_header("Summary", level=2)
page3.add_text("Summary and notes can be addd here.")
page3.add_header("About StaticDash", level=3)
page3.add_text("StaticDash is a lightweight static dashboard generator.")

# Page 4: Download
page4 = Page("download", "Download")
page4.add_header("Download Files", level=2)
page4.add_text("Here is a button to download a file.")
page4.add_download('./test_file.txt', "Download File")
page4.add_download('./test_file2.txt', "Download Another File")

# Demo Page with MiniPages (new usage)
page_demo = Page("demo", "MiniPage Combinations Demo")
page_demo.add_header("MiniPage Combinations", level=1)
page_demo.add_text("Below are examples of MiniPages with different content combinations:")

# Figures next to figures
mini_figs = MiniPage()
mini_figs.add_plot(fig1)
mini_figs.add_plot(fig2)
page_demo.add_minipage(mini_figs)

# Tables next to tables
mini_tables = MiniPage()
mini_tables.add_table(df)
mini_tables.add_table(df2)
page_demo.add_minipage(mini_tables)

# Table next to a figure
mini_table_fig = MiniPage()
mini_table_fig.add_table(df)
mini_table_fig.add_plot(fig1)
page_demo.add_minipage(mini_table_fig)

# Mixed: plot, table, plot
mini_mixed = MiniPage()
mini_mixed.add_plot(fig1)
mini_mixed.add_table(df)
mini_mixed.add_plot(fig2)
page_demo.add_minipage(mini_mixed)

# Register pages
dashboard.add_page(page1)
dashboard.add_page(page2)
dashboard.add_page(page3)
dashboard.add_page(page4)
dashboard.add_page(page_demo)

# Export
dashboard.publish(output_dir="output")