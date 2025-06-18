from staticdash.dashboard import Dashboard, Page
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

fig1 = px.bar(df, x="Category", y="Value", title="Bar Chart Example")
fig2 = px.line(df2, x="Time", y="Signal", title="Signal over Time")

# Build dashboard
dashboard = Dashboard(title="StaticDash Demo")

# Page 1: Overview
page1 = Page("overview", "Overview")
page1.add("Welcome to the StaticDash demo. Below is a bar chart and a table.")
page1.add(fig1)
page1.add(df)

# Page 2: Timeseries
page2 = Page("timeseries", "Timeseries")
page2.add("Here is a random time series with cumulative noise.")
page2.add(fig2)
page2.add(df2)

# Page 3: Summary
page3 = Page("summary", "Summary")
page3.add("Summary and notes can be added here.")
page3.add("StaticDash is a lightweight static dashboard generator.")

# Page 4: Download
page4 = Page("download", "Download")
page4.add("Here is a button to download a file.")
page4.add_download('./test_file.txt', "Download")

# Register pages
dashboard.add_page(page1)
dashboard.add_page(page2)
dashboard.add_page(page3)
dashboard.add_page(page4)

# Export
dashboard.publish(output_dir="output")