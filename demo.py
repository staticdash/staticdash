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

# Demo Page with MiniPages
mini1 = MiniPage(width=0.5)
mini1.add_header("Left", level=2)
mini1.add_text("Left content")

mini2 = MiniPage(width=0.5)
mini2.add_header("Right", level=2)
mini2.add_text("Right content")

row = MiniPage()
row.add_minipage(mini1)
row.add_minipage(mini2)

page_demo = Page("demo", "Demo Page")
page_demo.add_header("Demo", level=1)
page_demo.add_minipage(row)

# --- MiniPages: Figures next to figures ---
mini_fig1 = MiniPage(width=0.5)
mini_fig1.add_header("Bar Chart", level=3)
mini_fig1.add_plot(fig1)

mini_fig2 = MiniPage(width=0.5)
mini_fig2.add_header("Line Chart", level=3)
mini_fig2.add_plot(fig2)

row_figs = MiniPage()
row_figs.add_minipage(mini_fig1)
row_figs.add_minipage(mini_fig2)

# --- MiniPages: Tables next to tables ---
mini_table1 = MiniPage(width=0.5)
mini_table1.add_header("Category Table", level=3)
mini_table1.add_table(df)

mini_table2 = MiniPage(width=0.5)
mini_table2.add_header("Timeseries Table", level=3)
mini_table2.add_table(df2)

row_tables = MiniPage()
row_tables.add_minipage(mini_table1)
row_tables.add_minipage(mini_table2)

# --- MiniPages: Table next to a figure ---
mini_table = MiniPage(width=0.5)
mini_table.add_header("Category Table", level=3)
mini_table.add_table(df)

mini_fig = MiniPage(width=0.5)
mini_fig.add_header("Bar Chart", level=3)
mini_fig.add_plot(fig1)

row_table_fig = MiniPage()
row_table_fig.add_minipage(mini_table)
row_table_fig.add_minipage(mini_fig)

# --- Add all to a demo page ---
page_demo = Page("demo", "MiniPage Combinations Demo")
page_demo.add_header("MiniPage Combinations", level=1)
page_demo.add_text("Below are examples of MiniPages with different content combinations:")

page_demo.add_minipage(row_figs)
page_demo.add_minipage(row_tables)
page_demo.add_minipage(row_table_fig)

# Register pages
dashboard.add_page(page1)
dashboard.add_page(page2)
dashboard.add_page(page3)
dashboard.add_page(page4)
dashboard.add_page(page_demo)

# Export
dashboard.publish(output_dir="output")