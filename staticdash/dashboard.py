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
        # self.add_header(title, level=1)

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
    
    # def _track_outline(self, flowable):
    #     """
    #     Hook for collecting TOC entries and setting bookmarks.
    #     """
    #     from reportlab.platypus import Paragraph
    #     if isinstance(flowable, Paragraph):
    #         text = flowable.getPlainText()
    #         style_name = flowable.style.name
    #         if style_name.startswith("Heading"):
    #             try:
    #                 level = int(style_name.replace("Heading", ""))
    #             except ValueError:
    #                 return
    #             key = f"bookmark_{uuid.uuid4().hex}"
    #             flowable.canv.bookmarkPage(key)
    #             flowable.canv.addOutlineEntry(text, key, level=level - 1, closed=False)
    #             flowable._bookmarkName = key


    def _track_outline(self, canvas, doc):
        if hasattr(doc, '_last_heading'):
            level, text = doc._last_heading
            key = f"bookmark_{uuid.uuid4().hex}"
            canvas.bookmarkPage(key)
            canvas.addOutlineEntry(text, key, level=level - 1, closed=False)
            del doc._last_heading


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

    def publish_pdf(self, output_path="dashboard_report.pdf", pagesize="A4", include_toc=True, include_title_page=False, author=None, affiliation=None, title_page_marking=None):
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
        from reportlab.platypus.tableofcontents import TableOfContents
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from datetime import datetime
        import tempfile
        import io
        import os
        import plotly.io as pio

        pio.kaleido.scope.default_format = "png"

        page_size = A4 if pagesize.upper() == "A4" else letter
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']

        styles['Heading1'].fontSize = 18
        styles['Heading1'].spaceAfter = 12
        styles['Heading1'].spaceBefore = 18
        styles['Heading1'].fontName = 'Helvetica-Bold'

        styles['Heading2'].fontSize = 14
        styles['Heading2'].spaceAfter = 8
        styles['Heading2'].spaceBefore = 12
        styles['Heading2'].fontName = 'Helvetica-Bold'

        if 'CodeBlock' not in styles:
            styles.add(ParagraphStyle(
                name='CodeBlock',
                fontName='Courier',
                fontSize=9,
                leading=12,
                backColor=colors.whitesmoke,
                leftIndent=12,
                rightIndent=12,
                spaceAfter=8,
                borderPadding=4
            ))

        story = []

        class MyDocTemplate(SimpleDocTemplate):
            def __init__(self, *args, **kwargs):
                self.outline_entries = []
                self._outline_idx = 0
                super().__init__(*args, **kwargs)


            def afterFlowable(self, flowable):
                from reportlab.platypus import Paragraph
                if isinstance(flowable, Paragraph):
                    style_name = flowable.style.name
                    if style_name.startswith('Heading'):
                        try:
                            level = int(style_name.replace("Heading", ""))
                        except ValueError:
                            return  # Not a valid heading style

                        # Convert to outline level (0 = H1, 1 = H2, etc.)
                        outline_level = level - 1

                        # Clamp max to 2 for PDF outline safety
                        outline_level = max(0, min(outline_level, 2))

                        # Prevent skipping levels: ensure intermediates exist
                        # Track previous levels (add this as a class attribute if needed)
                        if not hasattr(self, "_last_outline_level"):
                            self._last_outline_level = -1

                        if outline_level > self._last_outline_level + 1:
                            outline_level = self._last_outline_level + 1  # prevent jump

                        self._last_outline_level = outline_level

                        text = flowable.getPlainText()
                        key = 'heading_%s' % self.seq.nextf('heading')
                        self.canv.bookmarkPage(key)
                        self.canv.addOutlineEntry(text, key, level=outline_level, closed=False)


                        self.notify('TOCEntry', (outline_level, text, self.page))



        def add_marking(canvas, doc, marking):
            if marking:
                canvas.saveState()
                canvas.setFont("Helvetica", 10)
                width, height = doc.pagesize
                text_width = canvas.stringWidth(marking, "Helvetica", 10)
                x = (width - text_width) / 2
                canvas.drawString(x, height - 36, marking)
                canvas.drawString(x, 36, marking)
                canvas.restoreState()

        if include_title_page:
            story.append(Spacer(1, 120))
            story.append(Paragraph(f"<b>{self.title}</b>", styles['Title']))
            story.append(Spacer(1, 48))
            lines = []
            if author:
                lines.append(str(author))
            if affiliation:
                lines.append(str(affiliation))
            lines.append(datetime.now().strftime('%B %d, %Y'))
            story.append(Paragraph("<para align='center'>" + "<br/>".join(lines) + "</para>", normal_style))
            story.append(PageBreak())

        if include_toc:
            toc = TableOfContents()
            toc.levelStyles = [
                ParagraphStyle(name='TOCHeading1', fontSize=14, leftIndent=20, firstLineIndent=-20, spaceBefore=10, leading=16),
                ParagraphStyle(name='TOCHeading2', fontSize=12, leftIndent=40, firstLineIndent=-20, spaceBefore=5, leading=12),
            ]
            story.append(Paragraph("Table of Contents", styles["Title"]))
            story.append(toc)
            story.append(PageBreak())

        def render_page(page, level=0, sec_prefix=[]):
            heading_style = styles['Heading1'] if level == 0 else styles['Heading2']

            # Only add the page.title as a real heading if it's a top-level page
            # if level == 0:
            #     story.append(Paragraph(page.title, heading_style))
            #     story.append(Spacer(1, 12))

            heading_style = styles['Heading1'] if level == 0 else styles['Heading2']
            story.append(Paragraph(page.title, heading_style))
            story.append(Spacer(1, 12))


            for kind, content, _ in page.elements:
                if kind == "text":
                    story.append(Paragraph(content, normal_style))
                    story.append(Spacer(1, 8))

                elif kind == "header":
                    text, lvl = content
                    safe_lvl = max(1, min(lvl + 1, 4))  # Clamp to Heading1–Heading4
                    style = styles[f'Heading{safe_lvl}']
                    story.append(Paragraph(text, style))
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
                        story.append(Paragraph("Table could not be rendered.", normal_style))

                elif kind == "plot":
                    fig = content
                    try:
                        if hasattr(fig, "savefig"):  # Matplotlib
                            buf = io.BytesIO()
                            fig.savefig(buf, format="png", bbox_inches="tight", dpi=300)
                            buf.seek(0)
                            story.append(Spacer(1, 8))
                            story.append(Image(buf, width=6*inch, height=4.5*inch))
                            story.append(Spacer(1, 12))
                        elif hasattr(fig, "write_image"):  # Plotly
                            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
                                fig.write_image(tmpfile.name, width=600, height=360, scale=2)
                                with open(tmpfile.name, "rb") as f:
                                    story.append(Spacer(1, 8))
                                    story.append(Image(io.BytesIO(f.read()), width=6*inch, height=3.6*inch))
                                    story.append(Spacer(1, 12))
                            os.unlink(tmpfile.name)
                    except Exception as e:
                        story.append(Paragraph(f"Plot rendering failed: {e}", normal_style))

                elif kind == "syntax":
                    code, language = content
                    from html import escape
                    story.append(Paragraph(f"<b>Code ({language}):</b>", normal_style))
                    story.append(Spacer(1, 4))
                    code_html = escape(code).replace(" ", "&nbsp;").replace("\n", "<br/>")
                    story.append(Paragraph(f"<font face='Courier'>{code_html}</font>", styles['CodeBlock']))
                    story.append(Spacer(1, 12))

                elif kind == "minipage":
                    render_page(content, level=level + 1, sec_prefix=sec_prefix)

            for child in page.children:
                story.append(PageBreak())
                render_page(child, level=level + 1, sec_prefix=sec_prefix + [1])


            story.append(PageBreak())

        for page in self.pages:
            render_page(page)



        doc = MyDocTemplate(
            output_path,
            pagesize=page_size,
            rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72,
        )

        doc.multiBuild(
            story,
            onFirstPage=lambda canvas, doc: add_marking(canvas, doc, title_page_marking),
            onLaterPages=lambda canvas, doc: add_marking(canvas, doc, self.marking)
        )
