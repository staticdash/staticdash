# simpledash

simpledash is a lightweight Python module for creating static, multi-page HTML dashboards. It supports Plotly plots, tables, and text content, with a fixed sidebar for navigation.

## Installation

Clone the repository and install it in editable mode:

```bash
git clone https://github.com/briday1/simpledash.git 
cd simpledash
pip install .
```

## Usage

Create a Python script like this:

```python
from simpledash.dashboard import Dashboard, Page
import plotly.graph_objects as go
import pandas as pd

# Initialize the dashboard
dashboard = Dashboard(title="SimpleDash Demo")

# Page 1: Plot
page1 = Page("overview", "Overview", "This is an overview of the data.")
fig = go.Figure()
fig.add_trace(go.Scatter(x=[1, 2, 3], y=[10, 20, 15], mode='lines+markers'))
page1.add_plot(fig)
dashboard.add_page(page1)

# Page 2: Table
page2 = Page("data", "Data Table", "Here is a table.")
df = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Score": [85, 92, 78]
})
page2.add_table(df)
dashboard.add_page(page2)

# Page 3: Text
page3 = Page("notes", "Notes", "Additional notes or text.")
page3.add_text("You can include plain text sections here.")
dashboard.add_page(page3)

# Generate the dashboard
dashboard.publish(output_dir="output")
```

After running the script, open output/index.html in your browser.