import os
import shutil
import uuid
import pandas as pd
import plotly.graph_objects as go
from dominate import document
from dominate.tags import div, h1, h2, h3, h4, p, a, script, link
from dominate.util import raw as raw_util
import html

class AbstractPage:
    def __init__(self):
        self.elements = []

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

    def add_minipage(self, minipage):
        self.elements.append(("minipage", minipage))

    def add_syntax(self, code, language="python"):
        self.elements.append(("syntax", (code, language)))

class Page(AbstractPage):
    def __init__(self, slug, title):
        super().__init__()
        self.slug = slug
        self.title = title
        self.add_header(title, level=1)

    def render(self, index):
        section = div()
        minipage_row = []
        for kind, content in self.elements:
            if kind == "minipage":
                row_div = div(cls="minipage-row")
                row_div += content.render(index)
                section += row_div
            elif kind == "header":
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
            elif kind == "download":
                file_path, label = content
                btn = a(label or os.path.basename(file_path),
                        href=file_path,
                        cls="download-button",
                        download=True)
                section += div(btn)
            elif kind == "syntax":
                code, language = content
                # Add a wrapper div for buttons and code
                code_id = f"code-{uuid.uuid4().hex[:8]}"
                toolbar = div(cls="code-toolbar")
                toolbar += a("Copy", href="#", cls="copy-btn", **{"data-target": code_id})
                toolbar += a("View Raw", href="#", cls="view-raw-btn", **{"data-target": code_id, "style": "margin-left:10px;"})

                escaped_code = html.escape(code)
                code_block = div(
                    toolbar,
                    raw_util(f'<pre><code id="{code_id}" class="language-{language}">{escaped_code}</code></pre>'),
                    cls="syntax-block"
                )
                section += raw_util(str(code_block))
        return section

class MiniPage(AbstractPage):
    def __init__(self):
        super().__init__()

    def render(self, index=None):
        row_div = div(cls="minipage-row")
        for kind, content in self.elements:
            cell = div(cls="minipage-cell")
            if kind == "header":
                text, level = content
                if level == 1:
                    cell += h1(text)
                elif level == 2:
                    cell += h2(text)
                elif level == 3:
                    cell += h3(text)
                elif level == 4:
                    cell += h4(text)
            elif kind == "text":
                cell += p(content)
            elif kind == "plot":
                cell += div(content, cls="plot-container")
            elif kind == "table":
                table_html, _ = content
                cell += raw_util(table_html)
            elif kind == "download":
                file_path, label = content
                btn = a(label or os.path.basename(file_path),
                        href=file_path,
                        cls="download-button",
                        download=True)
                cell += div(btn)
            elif kind == "syntax":
                code, language = content
                pre = div(cls="syntax-container")
                pre += raw_util(f"<pre><code class='{language}'>{code}</code></pre>")
                cell += pre
            row_div += cell
        return row_div

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
                doc.head.add(script(src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"))

            with doc:
                with div(cls="page-section", id=f"page-{page.slug}"):
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
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"))
            # Add Prism.js and its theme
            index_doc.head.add(link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"))
            # Add language support as needed
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-javascript.min.js"))

        with index_doc:
            with div(id="sidebar"):
                h1(self.title)
                for page in self.pages:
                    a(page.title, cls="nav-link", href="#", **{"data-target": f"page-{page.slug}"})
                with div(id="sidebar-footer"):
                    a("Produced by staticdash", href="https://pypi.org/project/staticdash/", target="_blank")

            with div(id="content"):
                for idx, page in enumerate(self.pages):
                    with div(id=f"page-{page.slug}", cls="page-section", style="display:none;") as section:
                        rendered = page.render(idx)
                        section += rendered  # This is correct

        with open(os.path.join(output_dir, "index.html"), "w") as f:
            f.write(str(index_doc))