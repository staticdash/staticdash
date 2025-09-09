import os
import shutil
import uuid
import pandas as pd
import plotly.graph_objects as go
from dominate import document
from dominate.tags import div, h1, h2, h3, h4, p, a, script, link, span
from dominate.util import raw as raw_util
import html
import io
import base64

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
        self.elements.append(("plot", plot, width))

    def add_table(self, df, table_id=None, sortable=True, width=None):
        self.elements.append(("table", df, width))

    def add_download(self, file_path, label=None, width=None):
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        self.elements.append(("download", (file_path, label), width))

    def add_minipage(self, minipage, width=None):
        self.elements.append(("minipage", minipage, width))

    def add_syntax(self, code, language="python", width=None):
        self.elements.append(("syntax", (code, language), width))


class Page(AbstractPage):
    def __init__(self, slug, title, page_width=None, marking=None):
        super().__init__()
        self.slug = slug
        self.title = title
        self.page_width = page_width
        self.marking = marking  # None => inherit dashboard; str => override
        self.children = []

    def add_subpage(self, page):
        self.children.append(page)

    def render(
        self,
        index,
        downloads_dir=None,
        relative_prefix="",
        inherited_width=None,
        inherited_marking=None,
        inherited_distribution=None
    ):
        effective_width = self.page_width or inherited_width
        effective_marking = self.marking if (self.marking is not None) else inherited_marking
        effective_distribution = getattr(self, "distribution", None) or inherited_distribution

        elements = []

        # Only show bars if a marking is present (no default text at all).
        if effective_marking:
            # Center within the MAIN CONTENT AREA (exclude sidebar and #content padding):
            # left  = sidebar_width + content_padding_x
            # width = viewport - sidebar_width - 2*content_padding_x
            shared_pos = (
                "position: fixed; "
                "left: calc(var(--sidebar-width, 240px) + var(--content-padding-x, 20px)); "
                "width: calc(100vw - var(--sidebar-width, 240px) - 2*var(--content-padding-x, 20px)); "
                "text-align: center; "
                "background-color: #f8f9fa; "
                "padding: 10px; "
                "z-index: 1000; "
                "font-weight: normal;"
            )

            elements.append(div(
                effective_marking,
                cls="floating-header",
                style=f"{shared_pos} top: 0;"
            ))

            footer_block = []
            if effective_distribution:
                footer_block.append(div(effective_distribution, style="margin-bottom: 4px; font-size: 10pt;"))
            footer_block.append(div(effective_marking))

            elements.append(div(
                *footer_block,
                cls="floating-footer",
                style=f"{shared_pos} bottom: 0;"
            ))

        # Render elements
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
                fig = content
                if hasattr(fig, "to_html"):
                    # Use local Plotly loaded in <head>
                    elem = div(raw_util(fig.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True})))
                else:
                    try:
                        buf = io.BytesIO()
                        fig.savefig(buf, format="png", bbox_inches="tight")
                        buf.seek(0)
                        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                        buf.close()
                        elem = div(
                            raw_util(f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%;">'),
                            style="display: flex; justify-content: center; align-items: center;"
                        )
                    except Exception as e:
                        elem = div(f"Matplotlib figure could not be rendered: {e}")
            elif kind == "table":
                df = content
                try:
                    html_table = df.to_html(classes="table-hover table-striped", index=False, border=0, table_id=f"table-{index}", escape=False)
                    elem = div(raw_util(html_table))
                except Exception as e:
                    elem = div(f"Table could not be rendered: {e}")
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
                elem = content.render(
                    index,
                    downloads_dir=downloads_dir,
                    relative_prefix=relative_prefix,
                    inherited_width=effective_width,
                    inherited_marking=effective_marking,
                    inherited_distribution=effective_distribution
                )
            if el_width is not None:
                elem = div(elem, style=style)
                elem = div(elem, style=outer_style)
            elements.append(elem)

        # Expose --content-width if you need it later, but centering no longer depends on it
        wrapper_style = (
            f"max-width: {effective_width}px; "
            "margin: 0 auto; width: 100%; "
            "padding-top: 80px; padding-bottom: 80px; "
            f"--content-width: {effective_width}px;"
        )
        wrapper = div(*elements, style=wrapper_style)
        return [wrapper]


class MiniPage(AbstractPage):
    def __init__(self, page_width=None):
        super().__init__()
        self.page_width = page_width

    def render(self, index=None, downloads_dir=None, relative_prefix="", inherited_width=None, inherited_marking=None, inherited_distribution=None):
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
                fig = content
                if hasattr(fig, "to_html"):
                    # Use local Plotly loaded in <head>
                    elem = div(raw_util(fig.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True})))
                else:
                    try:
                        buf = io.BytesIO()
                        fig.savefig(buf, format="png", bbox_inches="tight")
                        buf.seek(0)
                        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                        buf.close()
                        elem = div(
                            raw_util(f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%;">'),
                            style="display: flex; justify-content: center; align-items: center;"
                        )
                    except Exception as e:
                        elem = div(f"Matplotlib figure could not be rendered: {e}")
            elif kind == "table":
                df = content
                html_table = df.to_html(classes="table-hover table-striped", index=False, border=0, table_id=f"table-{index}", escape=False)
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
                elem = content.render(
                    index,
                    downloads_dir=downloads_dir,
                    relative_prefix=relative_prefix,
                    inherited_width=effective_width,
                    inherited_marking=inherited_marking,
                    inherited_distribution=inherited_distribution
                )
            if el_width is not None:
                elem = div(elem, style=style)
                elem = div(elem, style=outer_style)
            cell = div(elem, cls="minipage-cell")
            row_div += cell
        return row_div


class Dashboard:
    def __init__(self, title="Dashboard", page_width=900, marking=None, distribution=None):
        self.title = title
        self.pages = []
        self.page_width = page_width
        self.marking = marking            # Dashboard-wide default (None => no marking)
        self.distribution = distribution  # Dashboard-wide distribution statement

    def add_page(self, page):
        self.pages.append(page)

    def _render_sidebar(self, pages, prefix="", current_slug=None):
        # Structure preserved for your JS/CSS:
        # <div class="sidebar-group [open]">
        #   <a class="nav-link sidebar-parent" href="...">
        #       <span class="sidebar-arrow"></span>Title
        #   </a>
        #   <div class="sidebar-children"> ... </div>
        # </div>
        for page in pages:
            page_href = f"{prefix}{page.slug}.html"
            is_active = (page.slug == current_slug)

            def has_active_child(pg):
                return any(
                    child.slug == current_slug or has_active_child(child)
                    for child in getattr(pg, "children", [])
                )

            group_open = has_active_child(page)
            link_classes = "nav-link"
            if getattr(page, "children", []):
                link_classes += " sidebar-parent"
            if is_active:
                link_classes += " active"

            if getattr(page, "children", []):
                group_cls = "sidebar-group"
                if group_open or is_active:
                    group_cls += " open"
                with div(cls=group_cls):
                    a([
                        span("", cls="sidebar-arrow"),  # pure-CSS triangle (no Unicode)
                        page.title
                    ], cls=link_classes, href=page_href)
                    with div(cls="sidebar-children"):
                        self._render_sidebar(page.children, prefix, current_slug)
            else:
                a(page.title, cls=link_classes, href=page_href)

    def publish(self, output_dir="output"):
        output_dir = os.path.abspath(output_dir)
        pages_dir = os.path.join(output_dir, "pages")
        downloads_dir = os.path.join(output_dir, "downloads")
        assets_src = os.path.join(os.path.dirname(__file__), "assets")
        assets_dst = os.path.join(output_dir, "assets")

        os.makedirs(pages_dir, exist_ok=True)
        os.makedirs(downloads_dir, exist_ok=True)
        shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)

        def _add_head_assets(head, rel_prefix, effective_width):
            # Your CSS/JS
            head.add(link(rel="stylesheet", href=f"{rel_prefix}assets/css/style.css"))
            head.add(script(type="text/javascript", src=f"{rel_prefix}assets/js/script.js"))

            # MathJax: config for $...$ and $$...$$, then local bundle
            head.add(raw_util(
                "<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}};</script>"
            ))
            head.add(script(src=f"{rel_prefix}assets/vendor/mathjax/tex-mml-chtml.js"))

            # Prism (theme + core + languages) — all local
            head.add(link(rel="stylesheet", href=f"{rel_prefix}assets/vendor/prism/prism-tomorrow.min.css"))
            head.add(script(src=f"{rel_prefix}assets/vendor/prism/prism.min.js"))
            head.add(script(src=f"{rel_prefix}assets/vendor/prism/components/prism-python.min.js"))
            head.add(script(src=f"{rel_prefix}assets/vendor/prism/components/prism-javascript.min.js"))

            # Plotly local bundle (figs use include_plotlyjs=False)
            head.add(script(src=f"{rel_prefix}assets/vendor/plotly/plotly.min.js"))

            # Defaults that match your CSS; override in CSS if they change
            head.add(raw_util("<style>:root{--sidebar-width:240px;--content-padding-x:20px;}</style>"))
            head.add(raw_util(f"<style>.content-inner {{ max-width: {effective_width}px !important; }}</style>"))

        def write_page(page):
            doc = document(title=page.title)
            effective_width = page.page_width or self.page_width or 900
            with doc.head:
                _add_head_assets(doc.head, rel_prefix="../", effective_width=effective_width)
            with doc:
                with div(id="sidebar"):
                    a(self.title, href="../index.html", cls="sidebar-title")
                    self._render_sidebar(self.pages, prefix="", current_slug=page.slug)
                    with div(id="sidebar-footer"):
                        a("Produced by staticdash", href="../index.html")
                with div(id="content"):
                    with div(cls="content-inner"):
                        for el in page.render(
                            0,
                            downloads_dir=downloads_dir,
                            relative_prefix="../",
                            inherited_width=self.page_width,
                            inherited_marking=self.marking,
                            inherited_distribution=self.distribution
                        ):
                            div(el)

            with open(os.path.join(pages_dir, f"{page.slug}.html"), "w", encoding="utf-8") as f:
                f.write(str(doc))

            for child in getattr(page, "children", []):
                write_page(child)

        for page in self.pages:
            write_page(page)

        # Index page (first page)
        index_doc = document(title=self.title)
        effective_width = self.pages[0].page_width or self.page_width or 900
        with index_doc.head:
            _add_head_assets(index_doc.head, rel_prefix="", effective_width=effective_width)
        with index_doc:
            with div(id="sidebar"):
                a(self.title, href="index.html", cls="sidebar-title")
                self._render_sidebar(self.pages, prefix="pages/", current_slug=self.pages[0].slug)
                with div(id="sidebar-footer"):
                    a("Produced by staticdash", href="index.html")
            with div(id="content"):
                with div(cls="content-inner"):
                    for el in self.pages[0].render(
                        0,
                        downloads_dir=downloads_dir,
                        relative_prefix="",
                        inherited_width=self.page_width,
                        inherited_marking=self.marking,
                        inherited_distribution=self.distribution
                    ):
                        div(el)

        with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(str(index_doc))
