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
import plotly.graph_objects as go
import pandas as pd

# Create the dashboard
dashboard = Dashboard(title="StaticDash Demo")

# Page 1: Overview
page1 = Page("overview", "Overview")

# Add plo
fig = go.Figure()
fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 1, 6], mode='lines+markers', name="Demo Line"))
fig.update_layout(title="Sample Plot")
page1.append(fig)

# Add table
df1 = pd.DataFrame({
    "Category": ["A", "B", "C"],
    "Value": [100, 200, 150]
})
page1.append(df1)

# Add extra text
page1.append("This page includes a sample plot, table, and descriptive text.")
dashboard.add_page(page1)

# Page 2: Data Table
page2 = Page("data", "Data")
df2 = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Score": [85, 92, 78],
    "Passed": [True, True, False]
})
page2.append("This table shows individual scores and pass/fail status.")
page2.append(df2)
dashboard.add_page(page2)

# Page 3: Notes
page3 = Page("notes", "Notes")
page3.append("These are concluding notes about the dataset.")
page3.append("You can also add multiple text blocks like this.")
dashboard.add_page(page3)

# Publish the dashboard
dashboard.publish(output_dir="output")
```

After running the script, open output/index.html in your browser.