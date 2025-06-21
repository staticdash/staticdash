import os
import shutil
import uuid
import pandas as pd
import plotly.graph_objects as go
from dominate import document
from dominate.tags import div, h1, h2, h3, h4, p, a, script, link, table, thead, tr, th, tbody, td, span
from dominate.util import raw as raw_util

class Page:
    def __init__(self, slug, title):
        self.slug = slug
        self.title = title
        self.elements = []
        self.add_header(title, level=1)  # Add page title as level 1 header

    def add_header(self, text, level=1):
        if level not in (1, 2, 3, 4):
            raise ValueError("Header level must be 1, 2, 3, or 4")
        self.elements.append(("header", (text, level)))

    def add_text(self, text):
        self.elements.append(("text", text))

    def add_plot(self, plot):
        html = raw_util(plot.to_html(full_html=False, include_plotlyjs='cdn', config={'responsive': True}))
        self.elements.append(("plot", html))

    def add_table(self, df, table_id=None, sortable=True):
        if table_id is None:
            table_id = f"table-{len(self.elements)}"
        classes = "table-hover table-striped"
        if sortable:
            classes += " sortable"
        html = df.to_html(classes=classes, index=False, border=0, table_id=table_id, escape=False)
        self.elements.append(("table", (html, table_id)))

    def add_download(self, file_path, label=None):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        self.elements.append(("download", (file_path, label)))

    def add(self, element):
        if isinstance(element, str):
            self.add_text(element)
        elif isinstance(element, go.Figure):
            self.add_plot(element)
        elif isinstance(element, pd.DataFrame):
            self.add_table(element)
        else:
            raise ValueError(f"Unsupported element type: {type(element)}")

    def render(self, index):
        section = div(id=f"page-{index}", cls="page-section")
        for kind, content in self.elements:
            if kind == "header":
                text, level = content
                if level == 1:
                    section += h1(text)
                elif level == 2:
                    section += h2(text)
                elif level == 3:
                    section += h3(text)
                elif level == 4:
                    section += h4(text)
            elif kind == "text":
                section += p(content)
            elif kind == "plot":
                section += div(content, cls="plot-container")
            elif kind == "table":
                table_html, _ = content
                section += raw_util(table_html)
        return section

class Dashboard:
    def __init__(self, title="Dashboard"):
        self.title = title
        self.pages = []

    def add_page(self, page: Page):
        self.pages.append(page)

    def publish(self, output_dir="output"):
        output_dir = os.path.abspath(output_dir)
        pages_dir = os.path.join(output_dir, "pages")
        downloads_dir = os.path.join(output_dir, "downloads")
        assets_src = os.path.join(os.path.dirname(__file__), "assets")
        assets_dst = os.path.join(output_dir, "assets")

        os.makedirs(pages_dir, exist_ok=True)
        os.makedirs(downloads_dir, exist_ok=True)
        shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)

        for page in self.pages:
            doc = document(title=page.title)
            with doc.head:
                doc.head.add(link(rel="stylesheet", href="../assets/css/style.css"))
                doc.head.add(script(type="text/javascript", src="../assets/js/script.js"))

            with doc:
                with div(cls="page-section", id=f"page-{page.slug}"):
                    # Remove h1(page.title) here, since it's already a header element
                    for kind, content in page.elements:
                        if kind == "header":
                            text, level = content
                            if level == 1:
                                h1(text)
                            elif level == 2:
                                h2(text)
                            elif level == 3:
                                h3(text)
                            elif level == 4:
                                h4(text)
                        elif kind == "text":
                            p(content)
                        elif kind == "plot":
                            div(content, cls="plot-container")
                        elif kind == "table":
                            table_html, _ = content
                            doc.add(raw_util(table_html))

            with open(os.path.join(pages_dir, f"{page.slug}.html"), "w") as f:
                f.write(str(doc))

        index_doc = document(title=self.title)
        with index_doc.head:
            index_doc.head.add(link(rel="stylesheet", href="assets/css/style.css"))
            index_doc.head.add(script(type="text/javascript", src="assets/js/script.js"))

        with index_doc:
            with div(id="sidebar"):
                h1(self.title)
                for page in self.pages:
                    a(page.title, cls="nav-link", href="#", **{"data-target": f"page-{page.slug}"})
                with div(id="sidebar-footer"):
                    a("Produced by staticdash", href="https://pypi.org/project/staticdash/", target="_blank")

            with div(id="content"):
                for page in self.pages:
                    with div(id=f"page-{page.slug}", cls="page-section", style="display:none;"):
                        # Remove h2(page.title) here, since it's already a header element
                        for kind, content in page.elements:
                            if kind == "header":
                                text, level = content
                                if level == 1:
                                    h1(text)
                                elif level == 2:
                                    h2(text)
                                elif level == 3:
                                    h3(text)
                                elif level == 4:
                                    h4(text)
                            elif kind == "text":
                                p(content)
                            elif kind == "plot":
                                div(content, cls="plot-container")
                            elif kind == "table":
                                table_html, _ = content
                                div(raw_util(table_html))
                            elif kind == "download":
                                src_path, label = content
                                file_uuid = f"{uuid.uuid4().hex}_{os.path.basename(src_path)}"
                                dst_path = os.path.join(downloads_dir, file_uuid)
                                shutil.copy2(src_path, dst_path)
                                download_link = f"downloads/{file_uuid}"
                                btn = a(label or os.path.basename(src_path),
                                        href=download_link,
                                        cls="download-button",
                                        download=True)
                                div(btn)
                                div(raw_util("<br>"))

        with open(os.path.join(output_dir, "index.html"), "w") as f:
            f.write(str(index_doc))