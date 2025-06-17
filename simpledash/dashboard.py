import os
import shutil
import dominate
from dominate.tags import div, h1, h2, p, a, script, link, table, thead, tr, th, tbody, td
from dominate.util import raw  # ✅ correct usage

import plotly.graph_objs as go
import pandas as pd


class Page:
    def __init__(self, slug, title):
        self.slug = slug
        self.title = title
        self.elements = []

    def append(self, element):
        if isinstance(element, str):
            self.elements.append(p(element))
        elif isinstance(element, go.Figure):
            html = element.to_html(include_plotlyjs=False, full_html=False)
            self.elements.append(raw(html))
        elif isinstance(element, pd.DataFrame):
            tbl = table()
            tbl.add(thead(tr(*[th(col) for col in element.columns])))
            tb = tbody()
            for _, row in element.iterrows():
                tb.add(tr(*[td(str(val)) for val in row]))
            tbl.add(tb)
            self.elements.append(tbl)
        else:
            self.elements.append(element)


class Dashboard:
    def __init__(self, title="Dashboard"):
        self.title = title
        self.pages = []

    def add_page(self, page):
        self.pages.append(page)

    def publish(self, output_dir="output"):
        os.makedirs(output_dir, exist_ok=True)
        self._write_assets(output_dir)
        self._write_index(output_dir)

    def _write_assets(self, output_dir):
        css_src = os.path.join(os.path.dirname(__file__), "assets", "css", "style.css")
        css_dst_dir = os.path.join(output_dir, "assets", "css")
        os.makedirs(css_dst_dir, exist_ok=True)
        shutil.copyfile(css_src, os.path.join(css_dst_dir, "style.css"))

    def _write_index(self, output_dir):
        doc = dominate.document(title=self.title)

        with doc.head:
            link(rel="stylesheet", href="assets/css/style.css")
            script(src="https://cdn.plot.ly/plotly-latest.min.js")

        with doc:
            with div(id="sidebar"):
                h1(self.title)
                for i, page in enumerate(self.pages):
                    a(page.title, href="#", cls="nav-link", onclick=f"showPage('page-{i}')")

            with div(id="content"):
                for i, page in enumerate(self.pages):
                    section = div(id=f"page-{i}", cls="page-section")
                    section.add(h2(page.title))
                    for elem in page.elements:
                        section.add(elem)

        # JavaScript block
        js_code = """
        function showPage(id) {
          document.querySelectorAll('.page-section').forEach(el => el.style.display = 'none');
          document.getElementById(id).style.display = 'block';
          document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
          event.target.classList.add('active');
        }
        window.onload = () => showPage('page-0');
        """
        with doc:
            script(raw(js_code))

        with open(os.path.join(output_dir, "index.html"), "w") as f:
            f.write(doc.render())