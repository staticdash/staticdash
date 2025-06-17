# staticdash 

staticdash is a lightweight Python module for creating static, multi-page HTML dashboards. It supports Plotly plots, tables, and text content, with a fixed sidebar for navigation.

## Installation

Clone the repository and install it in editable mode:

```bash
git clone https://github.com/briday1/staticdash.git 
cd staticdash
pip install .
```

## Usage

Create a Python script like this:

```python
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

# Register pages
dashboard.add_page(page1)
dashboard.add_page(page2)
dashboard.add_page(page3)

# Export
dashboard.publish(output_dir="output")
```

After running the script, open output/index.html in your browser.