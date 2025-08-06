import os
import shutil
import uuid
import pandas as pd
import plotly.graph_objects as go
from dominate import document
from dominate.tags import div, h1, h2, h3, h4, p, a, script, link, span
from dominate.util import raw as raw_util
import html
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import tempfile
import matplotlib.pyplot as plt
import io, base64

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
        self.marking = marking  # Page-specific marking
        self.children = []
        self.add_header(title, level=1)

    def add_subpage(self, page):
        self.children.append(page)

    def render(self, index, downloads_dir=None, relative_prefix="", inherited_width=None):
        effective_width = self.page_width or inherited_width
        elements = []

        # Add floating header and footer for marking
        marking = self.marking or "Default Marking"
        elements.append(div(
            marking,
            cls="floating-header",
            style="position: fixed; top: 0; left: 50%; transform: translateX(-50%); width: auto; background-color: #f8f9fa; text-align: center; padding: 10px; z-index: 1000; font-weight: normal;"
        ))
        elements.append(div(
            marking,
            cls="floating-footer",
            style="position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: auto; background-color: #f8f9fa; text-align: center; padding: 10px; z-index: 1000; font-weight: normal;"
        ))

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
                    elem = div(raw_util(fig.to_html(full_html=False, include_plotlyjs='cdn', config={'responsive': True})))
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
                elem = content.render(index, downloads_dir=downloads_dir, relative_prefix=relative_prefix, inherited_width=effective_width)
            if el_width is not None:
                elem = div(elem, style=style)
                elem = div(elem, style=outer_style)
            elements.append(elem)

        # Add padding to avoid overlap with header and footer
        wrapper = div(*elements, style=f"max-width: {effective_width}px; margin: 0 auto; width: 100%; padding-top: 80px; padding-bottom: 80px;")
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
                fig = content
                # Plotly support (existing)
                if hasattr(fig, "to_html"):
                    elem = div(raw_util(fig.to_html(full_html=False, include_plotlyjs='cdn', config={'responsive': True})))
                # Matplotlib support
                else:
                    try:
                        buf = io.BytesIO()
                        fig.savefig(buf, format="png", bbox_inches="tight")
                        buf.seek(0)
                        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                        buf.close()
                        # Center the image using a div with inline styles
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
                elem = content.render(index, downloads_dir=downloads_dir, relative_prefix=relative_prefix, inherited_width=effective_width)
            if el_width is not None:
                elem = div(elem, style=style)
                elem = div(elem, style=outer_style)
            cell = div(elem, cls="minipage-cell")
            row_div += cell
        return row_div

class Dashboard:
    def __init__(self, title="Dashboard", page_width=900, marking=None):
        self.title = title
        self.pages = []
        self.page_width = page_width
        self.marking = marking  # Dashboard-wide marking

    def add_page(self, page):
        self.pages.append(page)

    def _render_sidebar(self, pages, prefix="", current_slug=None):
        for page in pages:
            page_href = f"{prefix}{page.slug}.html"
            is_active = (page.slug == current_slug)
            def has_active_child(page):
                return any(
                    child.slug == current_slug or has_active_child(child)
                    for child in getattr(page, "children", [])
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
                        span("▶", cls="sidebar-arrow"),
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

        def write_page(page):
            doc = document(title=page.title)
            effective_width = page.page_width or self.page_width or 900
            with doc.head:
                doc.head.add(link(rel="stylesheet", href="../assets/css/style.css"))
                doc.head.add(script(type="text/javascript", src="../assets/js/script.js"))
                doc.head.add(script(src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"))
                doc.head.add(link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css"))
                doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"))
                doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"))
                doc.head.add(script(src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-javascript.min.js"))
                # Inject dynamic page width
                doc.head.add(raw_util(f"<style>.content-inner {{ max-width: {effective_width}px !important; }}</style>"))
            with doc:
                with div(id="sidebar"):
                    a(self.title, href="../index.html", cls="sidebar-title")
                    self._render_sidebar(self.pages, prefix="", current_slug=page.slug)
                    with div(id="sidebar-footer"):
                        a("Produced by staticdash", href="https://pypi.org/project/staticdash/", target="_blank")
                with div(id="content"):
                    with div(cls="content-inner"):
                        for el in page.render(0, downloads_dir=downloads_dir, relative_prefix="../"):
                            div(el)
            with open(os.path.join(pages_dir, f"{page.slug}.html"), "w") as f:
                f.write(str(doc))
            for child in getattr(page, "children", []):
                write_page(child)

        for page in self.pages:
            write_page(page)

        # Index page
        index_doc = document(title=self.title)
        effective_width = self.pages[0].page_width or self.page_width or 900
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
            # Inject dynamic page width
            index_doc.head.add(raw_util(f"<style>.content-inner {{ max-width: {effective_width}px !important; }}</style>"))
        with index_doc:
            with div(id="sidebar"):
                a(self.title, href="index.html", cls="sidebar-title")
                self._render_sidebar(self.pages, prefix="pages/", current_slug=self.pages[0].slug)
                with div(id="sidebar-footer"):
                    a("Produced by staticdash", href="https://pypi.org/project/staticdash/", target="_blank")
            with div(id="content"):
                with div(cls="content-inner"):
                    for el in self.pages[0].render(0, downloads_dir=downloads_dir, relative_prefix=""):
                        div(el)

        with open(os.path.join(output_dir, "index.html"), "w") as f:
            f.write(str(index_doc))

    def publish_pdf(self, output_path="dashboard_report.pdf", pagesize="A4", include_title_page=False, title_page_marking=None, author=None, affiliation=None):
        from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph, PageBreak, Image
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet
        from datetime import datetime
        import io

        page_size = A4 if pagesize == "A4" else letter
        styles = getSampleStyleSheet()
        story = []

        # Add title page
        if include_title_page:
            story.append(Spacer(1, 120))
            story.append(Paragraph(f"<b>{self.title}</b>", styles['Title']))
            story.append(Spacer(1, 48))

            # Center author, affiliation, and date
            if author:
                story.append(Paragraph(f"<para align='center'>{author}</para>", styles['Normal']))
            if affiliation:
                story.append(Paragraph(f"<para align='center'>{affiliation}</para>", styles['Normal']))
            current_date = datetime.now().strftime("%B %d, %Y")
            story.append(Paragraph(f"<para align='center'>{current_date}</para>", styles['Normal']))

            story.append(PageBreak())

        # Add markings to the PDF
        def add_marking(canvas, doc, marking):
            if marking:
                canvas.saveState()
                canvas.setFont("Helvetica", 10)
                page_width = doc.pagesize[0]
                text_width = canvas.stringWidth(marking, "Helvetica", 10)
                x_position = (page_width - text_width) / 2  # Center the marking
                canvas.drawString(x_position, doc.pagesize[1] - 36, marking)  # Header
                canvas.drawString(x_position, 36, marking)  # Footer
                canvas.restoreState()

        # Recursive function to render pages and subpages
        def render_page(page):
            # Render the current page
            for kind, content, _ in page.elements:
                if kind == "text":
                    story.append(Paragraph(content, styles['Normal']))
                    story.append(Spacer(1, 8))
                elif kind == "header":
                    text, level = content
                    header_style = styles[f'Heading{min(level + 1, 4)}']
                    story.append(Paragraph(text, header_style))
                    story.append(Spacer(1, 8))
                elif kind == "table":
                    df = content
                    try:
                        data = [df.columns.tolist()] + df.values.tolist()
                        t = Table(data, repeatRows=1)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#222C36")),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 11),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                            ('TOPPADDING', (0, 0), (-1, 0), 10),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#B0B8C1")),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 10),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ('TOPPADDING', (0, 1), (-1, -1), 6),
                            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 12))
                    except Exception:
                        story.append(Paragraph("Table could not be rendered.", styles['Normal']))
                elif kind == "plot":
                    fig = content
                    try:
                        # Handle Plotly figures
                        if hasattr(fig, "to_image"):
                            img_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
                            img_buffer = io.BytesIO(img_bytes)
                            img = Image(img_buffer, width=6 * inch, height=4.5 * inch)
                            story.append(img)
                            story.append(Spacer(1, 12))
                        # Handle Matplotlib figures
                        elif hasattr(fig, "savefig"):
                            buf = io.BytesIO()
                            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
                            buf.seek(0)
                            img = Image(buf, width=6 * inch, height=4.5 * inch)
                            story.append(img)
                            story.append(Spacer(1, 12))
                    except Exception as e:
                        story.append(Paragraph(f"Plot could not be rendered: {e}", styles['Normal']))
                elif kind == "syntax":
                    # Handle syntax blocks
                    pass
                elif kind == "minipage":
                    # Handle subpages
                    pass

            # Recursively render subpages
            for child in getattr(page, "children", []):
                story.append(PageBreak())  # Add a PageBreak before rendering subpages
                render_page(child)

        # Render all pages
        for page in self.pages:
            render_page(page)
            story.append(PageBreak())  # Add a PageBreak after each top-level page

        # Build the PDF
        doc = SimpleDocTemplate(output_path, pagesize=page_size)
        doc.build(
            story,
            onFirstPage=lambda canvas, doc: add_marking(canvas, doc, title_page_marking),
            onLaterPages=lambda canvas, doc: add_marking(canvas, doc, self.marking)
        )
