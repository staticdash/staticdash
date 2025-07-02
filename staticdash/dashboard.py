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

    def add_header(self, text, level=1, width=None):
        if level not in (1, 2, 3, 4):
            raise ValueError("Header level must be 1, 2, 3, or 4")
        self.elements.append(("header", (text, level), width))

    def add_text(self, text, width=None):
        self.elements.append(("text", text, width))

    def add_plot(self, plot, width=None):
        html_plot = plot.to_html(full_html=False, include_plotlyjs='cdn', config={'responsive': True})
        self.elements.append(("plot", html_plot, width))

    def add_table(self, df, table_id=None, sortable=True, width=None):
        if table_id is None:
            table_id = f"table-{len(self.elements)}"
        classes = "table-hover table-striped"
        if sortable:
            classes += " sortable"
        html_table = df.to_html(classes=classes, index=False, border=0, table_id=table_id, escape=False)
        self.elements.append(("table", (html_table, table_id), width))

    def add_download(self, file_path, label=None, width=None):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        self.elements.append(("download", (file_path, label), width))

    def add_minipage(self, minipage, width=None):
        self.elements.append(("minipage", minipage, width))

    def add_syntax(self, code, language="python", width=None):
        self.elements.append(("syntax", (code, language), width))

class Page(AbstractPage):
    def __init__(self, slug, title, page_width=None):
        super().__init__()
        self.slug = slug
        self.title = title
        self.page_width = page_width
        self.add_header(title, level=1)

    def render(self, index, downloads_dir=None, relative_prefix="", inherited_width=None):
        effective_width = self.page_width or inherited_width
        elements = []
        for kind, content, el_width in self.elements:
            style = ""
            outer_style = ""
            if el_width is not None:
                style = f"width: {el_width * 100}%;"
                outer_style = "display: flex; justify-content: center; margin: 0 auto;"
            elem = None
            if kind == "text":
                elem = p(content)  # always wrap text in a tag
            elif kind == "header":
                text, level = content
                header_tag = {1: h1, 2: h2, 3: h3, 4: h4}[level]
                elem = header_tag(text)
            elif kind == "plot":
                elem = div(raw_util(content))
            elif kind == "table":
                html_table, _ = content
                elem = div(raw_util(html_table))
            elif kind == "download":
                file_path, label = content
                btn = a(label or os.path.basename(file_path), href=file_path, cls="download-button", download=True)
                elem = div(btn)
            elif kind == "syntax":
                code, language = content
                elem = div(
                    raw_util(
                        f'<pre class="syntax-block"><code class="language-{language}">{html.escape(code)}</code></pre>'
                    ),
                    cls="syntax-block"
                )
            elif kind == "minipage":
                elem = content.render(index, downloads_dir=downloads_dir, relative_prefix=relative_prefix, inherited_width=effective_width)
            if el_width is not None:
                elem = div(elem, style=style)
                elem = div(elem, style=outer_style)
            elements.append(elem)
        wrapper = div(*elements, style=f"max-width: {effective_width}px; margin: 0 auto; width: 100%;")
        return [wrapper]

class MiniPage(AbstractPage):
    def __init__(self, page_width=None):
        super().__init__()
        self.page_width = page_width

    def render(self, index=None, downloads_dir=None, relative_prefix="", inherited_width=None):
        effective_width = self.page_width or inherited_width
        row_div = div(cls="minipage-row", style=f"max-width: {effective_width}px; margin: 0 auto; width: 100%;")
        for kind, content, el_width in self.elements:
            style = ""
            outer_style = ""
            if el_width is not None:
                style = f"width: {el_width * 100}%;"
                outer_style = "display: flex; justify-content: center; margin: 0 auto;"
            elem = None
            if kind == "text":
                elem = p(content)
            elif kind == "header":
                text, level = content
                header_tag = {1: h1, 2: h2, 3: h3, 4: h4}[level]
                elem = header_tag(text)
            elif kind == "plot":
                elem = raw_util(content)
            elif kind == "table":
                html_table, _ = content
                elem = raw_util(html_table)
            elif kind == "download":
                file_path, label = content
                btn = a(label or os.path.basename(file_path), href=file_path, cls="download-button", download=True)
                elem = div(btn)
            elif kind == "syntax":
                code, language = content
                elem = div(
                    raw_util(
                        f'<pre class="syntax-block"><code class="language-{language}">{html.escape(code)}</code></pre>'
                    ),
                    cls="syntax-block"
                )
            elif kind == "minipage":
                elem = content.render(index, downloads_dir=downloads_dir, relative_prefix=relative_prefix, inherited_width=effective_width)
            # Center and size if width is set
            if el_width is not None:
                elem = div(elem, style=style)
                elem = div(elem, style=outer_style)
            cell = div(elem, cls="minipage-cell")
            row_div += cell
        return row_div

class Dashboard:
    def __init__(self, title="Dashboard", page_width=900):
        self.title = title
        self.pages = []
        self.page_width = page_width  # in pixels

    def add_page(self, page):
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

        # Per-page HTML
        for page in self.pages:
            doc = document(title=page.title)
            with doc.head:
                doc.head.add(link(rel="stylesheet", href="../assets/css/style.css"))
                doc.head.add(script(type="text/javascript", src="../assets/js/script.js"))
                doc.head.add(script(src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"))
                doc.head.add(link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css"))
                doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"))
                doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"))
                doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-javascript.min.js"))
            with doc:
                with div(cls="page-section", id=f"page-{page.slug}") as section:
                    for el in page.render(0, downloads_dir=downloads_dir, relative_prefix="../"):
                        section += el
            with open(os.path.join(pages_dir, f"{page.slug}.html"), "w") as f:
                f.write(str(doc))

        # Main index.html
        index_doc = document(title=self.title)
        with index_doc.head:
            index_doc.head.add(link(rel="stylesheet", href="assets/css/style.css"))
            index_doc.head.add(script(type="text/javascript", src="assets/js/script.js"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"))
            index_doc.head.add(link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-javascript.min.js"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-sql.min.js"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-markup.min.js"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-bash.min.js"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-json.min.js"))
            index_doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-c.min.js"))

        with index_doc:
            with div(id="sidebar"):
                h1(self.title)
                for page in self.pages:
                    a(page.title, cls="nav-link", href="#", **{"data-target": f"page-{page.slug}"})
                with div(id="sidebar-footer"):
                    a("Produced by staticdash", href="https://pypi.org/project/staticdash/", target="_blank")

            with div(id="content"):
                with div(cls="content-inner"):
                    for idx, page in enumerate(self.pages):
                        with div(id=f"page-{page.slug}", cls="page-section", style="display:none;") as section:
                            for el in page.render(idx, downloads_dir=downloads_dir, relative_prefix=""):
                                section += el

        with open(os.path.join(output_dir, "index.html"), "w") as f:
            f.write(str(index_doc))