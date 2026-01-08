import os
import shutil
import uuid
import re
import pandas as pd
import plotly.graph_objects as go
from dominate import document
from dominate.tags import div, h1, h2, h3, h4, p, a, script, link, span
from dominate.util import raw as raw_util
import html
import io
import base64
import matplotlib
from matplotlib import rc_context

def split_paragraphs_preserving_math(text):
    """
    Split text into paragraphs on double newlines, preserving math expressions.
    Assumes math is in $...$ (inline) or $$...$$ (display) format.
    """
    math_blocks = []
    
    # Replace math with placeholders
    def replace_math(match):
        math_blocks.append(match.group(0))
        return f"__MATH_BLOCK_{len(math_blocks)-1}__"
    
    # Handle display math first ($$...$$), then inline ($...$)
    text = re.sub(r'\$\$([^$]+)\$\$', replace_math, text, flags=re.DOTALL)
    text = re.sub(r'\$([^$]+)\$', replace_math, text, flags=re.DOTALL)
    
    # Split on double newlines
    paragraphs = text.split('\n\n')
    
    # Restore math in each paragraph
    restored_paragraphs = []
    for para in paragraphs:
        for i, block in enumerate(math_blocks):
            para = para.replace(f"__MATH_BLOCK_{i}__", block)
        restored_paragraphs.append(para.strip())
    
    # Filter out empty paragraphs
    return [para for para in restored_paragraphs if para]

class AbstractPage:
    def __init__(self):
        self.elements = []

    def add_header(self, text, level=1, width=None):
        if level not in (1, 2, 3, 4):
            raise ValueError("Header level must be 1, 2, 3, or 4")
        self.elements.append(("header", (text, level), width))

    def add_text(self, text, width=None):
        self.elements.append(("text", text, width))

    def add_plot(self, plot, width=None, height=None, width_px=None, align="center"):
        # Keep backward-compatible: `width` is a fraction (0..1) of page width.
        # `height` is pixels (existing behavior). New optional `width_px`
        # (pixels) can be supplied to control plot width. `align` controls
        # horizontal alignment: 'left', 'center' (default), or 'right'.
        # We store a tuple (plot, height_px, width_px, align) for forward-compatibility.
        self.elements.append(("plot", (plot, height, width_px, align), width))

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
                paragraphs = split_paragraphs_preserving_math(content)
                if paragraphs:
                    elem = div(*[p(para) for para in paragraphs])
                else:
                    elem = p(content)
            elif kind == "header":
                text, level = content
                header_tag = {1: h1, 2: h2, 3: h3, 4: h4}[level]
                elem = header_tag(text)
            elif kind == "plot":
                # content may be stored as (figure, height), (figure, height, width_px)
                # or (figure, height, width_px, align)
                specified_height = None
                specified_width_px = None
                specified_align = "center"
                if isinstance(content, (list, tuple)):
                    if len(content) == 4:
                        fig, specified_height, specified_width_px, specified_align = content
                    elif len(content) == 3:
                        fig, specified_height, specified_width_px = content
                    elif len(content) == 2:
                        fig, specified_height = content
                    else:
                        fig = content
                else:
                    fig = content

                if hasattr(fig, "to_html"):
                    # Use local Plotly loaded in <head>
                    # Ensure the figure uses a robust font family so minus signs and other
                    # glyphs render correctly in the browser (some system fonts lack U+2212)
                    try:
                        font_family = None
                        if getattr(fig, 'layout', None) and getattr(fig.layout, 'font', None):
                            font_family = getattr(fig.layout.font, 'family', None)
                        if not font_family:
                            fig.update_layout(font_family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif')
                    except Exception:
                        # Be defensive: don't fail rendering if layout manipulation isn't available
                        pass

                    try:
                        # Temporarily set layout height/width if specified (pixels)
                        orig_height = None
                        orig_width = None
                        try:
                            orig_height = getattr(fig.layout, 'height', None)
                        except Exception:
                            orig_height = None
                        try:
                            orig_width = getattr(fig.layout, 'width', None)
                        except Exception:
                            orig_width = None

                        try:
                            if specified_height is not None:
                                fig.update_layout(height=specified_height)
                            if specified_width_px is not None:
                                fig.update_layout(width=specified_width_px)
                        except Exception:
                            pass

                        # If a local vendored Plotly exists, rely on the head script.
                        # Otherwise include Plotly from CDN so the inline newPlot call works.
                        vendor_plotly = os.path.join(os.path.dirname(__file__), "assets", "vendor", "plotly", "plotly.min.js")
                        include_plotly = False
                        if not os.path.exists(vendor_plotly):
                            include_plotly = "cdn"
                        plotly_html = fig.to_html(full_html=False, include_plotlyjs=include_plotly, config={'responsive': True})

                        # Wrap the Plotly HTML in a container with explicit pixel sizing
                        container_style = "width:100%;"
                        if specified_width_px is not None:
                            container_style = f"width:{specified_width_px}px;"
                        if specified_height is not None:
                            container_style = container_style + f" height:{specified_height}px;"

                        plot_wrapped = f'<div style="{container_style}">{plotly_html}</div>'
                        # Apply alignment wrapper
                        if specified_align not in ("left", "right", "center"):
                            specified_align = "center"
                        if specified_align == "center":
                            align_style = "display:flex; justify-content:center; align-items:center;"
                        elif specified_align == "left":
                            align_style = "display:flex; justify-content:flex-start; align-items:center;"
                        else:
                            align_style = "display:flex; justify-content:flex-end; align-items:center;"

                        outer = f'<div style="{align_style}">{plot_wrapped}</div>'
                        elem = div(raw_util(outer))

                        # restore original height/width if we changed them
                        try:
                            if specified_height is not None:
                                fig.update_layout(height=orig_height)
                            if specified_width_px is not None:
                                fig.update_layout(width=orig_width)
                        except Exception:
                            pass
                    except Exception as e:
                        elem = div(f"Plotly figure could not be rendered: {e}")
                else:
                    # Robust Matplotlib -> PNG path. Ensure `buf` exists and is closed.
                    buf = io.BytesIO()
                    try:
                        # If pixel width/height specified, attempt to adjust figure size
                        orig_size = None
                        try:
                            dpi = fig.get_dpi()
                        except Exception:
                            dpi = None
                        try:
                            if dpi is not None and (specified_height is not None or specified_width_px is not None):
                                orig_size = fig.get_size_inches()
                                new_w = orig_size[0]
                                new_h = orig_size[1]
                                if specified_width_px is not None:
                                    new_w = specified_width_px / dpi
                                if specified_height is not None:
                                    new_h = specified_height / dpi
                                fig.set_size_inches(new_w, new_h)
                        except Exception:
                            orig_size = None

                        with rc_context({"axes.unicode_minus": False}):
                            fig.savefig(buf, format="png", bbox_inches="tight")

                        # restore original size if changed
                        try:
                            if orig_size is not None:
                                fig.set_size_inches(orig_size)
                        except Exception:
                            pass

                        buf.seek(0)
                        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                        img_style = "max-width:100%;"
                        if specified_height is not None:
                            img_style = img_style + f" height:{specified_height}px;"
                        if specified_width_px is not None:
                            img_style = img_style + f" width:{specified_width_px}px;"

                        if specified_align not in ("left", "right", "center"):
                            specified_align = "center"
                        if specified_align == "center":
                            align_style = "display:flex; justify-content:center; align-items:center;"
                        elif specified_align == "left":
                            align_style = "display:flex; justify-content:flex-start; align-items:center;"
                        else:
                            align_style = "display:flex; justify-content:flex-end; align-items:center;"

                        elem = div(
                            raw_util(f'<img src="data:image/png;base64,{img_base64}" style="{img_style}">'),
                            style=align_style
                        )
                    except Exception as e:
                        elem = div(f"Matplotlib figure could not be rendered: {e}")
                    finally:
                        try:
                            buf.close()
                        except Exception:
                            pass
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
                paragraphs = split_paragraphs_preserving_math(content)
                if paragraphs:
                    elem = div(*[p(para) for para in paragraphs])
                else:
                    elem = p(content)
            elif kind == "header":
                text, level = content
                header_tag = {1: h1, 2: h2, 3: h3, 4: h4}[level]
                elem = header_tag(text)
            elif kind == "plot":
                # content may be stored as (figure, height) or (figure, height, width_px)
                specified_height = None
                specified_width_px = None
                if isinstance(content, (list, tuple)):
                    if len(content) == 3:
                        fig, specified_height, specified_width_px = content
                    elif len(content) == 2:
                        fig, specified_height = content
                    else:
                        fig = content
                else:
                    fig = content

                if hasattr(fig, "to_html"):
                    # Use local Plotly loaded in <head>
                    # Ensure the figure uses a robust font family so minus signs and other
                    # glyphs render correctly in the browser (some system fonts lack U+2212)
                    try:
                        font_family = None
                        if getattr(fig, 'layout', None) and getattr(fig.layout, 'font', None):
                            font_family = getattr(fig.layout.font, 'family', None)
                        if not font_family:
                            fig.update_layout(font_family='-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif')
                    except Exception:
                        pass
                    try:
                        orig_height = None
                        orig_width = None
                        try:
                            orig_height = getattr(fig.layout, 'height', None)
                        except Exception:
                            orig_height = None
                        try:
                            orig_width = getattr(fig.layout, 'width', None)
                        except Exception:
                            orig_width = None

                        try:
                            if specified_height is not None:
                                fig.update_layout(height=specified_height)
                            if specified_width_px is not None:
                                fig.update_layout(width=specified_width_px)
                        except Exception:
                            pass

                        vendor_plotly = os.path.join(os.path.dirname(__file__), "assets", "vendor", "plotly", "plotly.min.js")
                        include_plotly = False
                        if not os.path.exists(vendor_plotly):
                            include_plotly = "cdn"
                        plotly_html = fig.to_html(full_html=False, include_plotlyjs=include_plotly, config={'responsive': True})
                        container_style = "width:100%;"
                        if specified_width_px is not None:
                            container_style = f"width:{specified_width_px}px;"
                        if specified_height is not None:
                            container_style = container_style + f" height:{specified_height}px;"
                        plot_wrapped = f'<div style="{container_style}">{plotly_html}</div>'
                        if specified_align not in ("left", "right", "center"):
                            specified_align = "center"
                        if specified_align == "center":
                            align_style = "display:flex; justify-content:center; align-items:center;"
                        elif specified_align == "left":
                            align_style = "display:flex; justify-content:flex-start; align-items:center;"
                        else:
                            align_style = "display:flex; justify-content:flex-end; align-items:center;"
                        outer = f'<div style="{align_style}">{plot_wrapped}</div>'
                        elem = div(raw_util(outer))

                        try:
                            if specified_height is not None:
                                fig.update_layout(height=orig_height)
                            if specified_width_px is not None:
                                fig.update_layout(width=orig_width)
                        except Exception:
                            pass
                    except Exception as e:
                        elem = div(f"Plotly figure could not be rendered: {e}")
                else:
                    # Robust Matplotlib -> PNG path. Ensure `buf` exists and is closed.
                    buf = io.BytesIO()
                    try:
                        # If pixel width/height specified, attempt to adjust figure size
                        orig_size = None
                        try:
                            dpi = fig.get_dpi()
                        except Exception:
                            dpi = None
                        try:
                            if dpi is not None and (specified_height is not None or specified_width_px is not None):
                                orig_size = fig.get_size_inches()
                                new_w = orig_size[0]
                                new_h = orig_size[1]
                                if specified_width_px is not None:
                                    new_w = specified_width_px / dpi
                                if specified_height is not None:
                                    new_h = specified_height / dpi
                                fig.set_size_inches(new_w, new_h)
                        except Exception:
                            orig_size = None

                        with rc_context({"axes.unicode_minus": False}):
                            fig.savefig(buf, format="png", bbox_inches="tight")

                        # restore original size if changed
                        try:
                            if orig_size is not None:
                                fig.set_size_inches(orig_size)
                        except Exception:
                            pass

                        buf.seek(0)
                        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
                        img_style = "max-width:100%;"
                        if specified_height is not None:
                            img_style = img_style + f" height:{specified_height}px;"
                        if specified_width_px is not None:
                            img_style = img_style + f" width:{specified_width_px}px;"
                        if specified_align not in ("left", "right", "center"):
                            specified_align = "center"
                        if specified_align == "center":
                            align_style = "display:flex; justify-content:center; align-items:center;"
                        elif specified_align == "left":
                            align_style = "display:flex; justify-content:flex-start; align-items:center;"
                        else:
                            align_style = "display:flex; justify-content:flex-end; align-items:center;"
                        elem = div(
                            raw_util(f'<img src="data:image/png;base64,{img_base64}" style="{img_style}">'),
                            style=align_style
                        )
                    except Exception as e:
                        elem = div(f"Matplotlib figure could not be rendered: {e}")
                    finally:
                        try:
                            buf.close()
                        except Exception:
                            pass
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
                a(page.title, cls="nav-link", href=page_href)

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
            # Ensure pages declare UTF-8 to avoid character misinterpretation
            head.add(raw_util('<meta charset="utf-8" />'))
            head.add(raw_util('<meta name="viewport" content="width=device-width, initial-scale=1" />'))
            # Your CSS/JS
            head.add(link(rel="stylesheet", href=f"{rel_prefix}assets/css/style.css"))
            head.add(script(type="text/javascript", src=f"{rel_prefix}assets/js/script.js"))

            # MathJax: config for $...$ and $$...$$
            head.add(raw_util(
                "<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}};</script>"
            ))
            # Local-first, CDN-fallback (for editable installs without vendored files)
            head.add(raw_util(
                f"<script src=\"{rel_prefix}assets/vendor/mathjax/tex-svg.js\" "
                "onerror=\"var s=document.createElement('script');"
                "s.src='https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js';"
                "document.head.appendChild(s);\"></script>"
            ))

            # Prism (theme + core + languages) — still local
            head.add(link(rel="stylesheet", href=f"{rel_prefix}assets/vendor/prism/prism-tomorrow.min.css"))
            head.add(script(src=f"{rel_prefix}assets/vendor/prism/prism.min.js"))
            head.add(script(src=f"{rel_prefix}assets/vendor/prism/components/prism-python.min.js"))
            head.add(script(src=f"{rel_prefix}assets/vendor/prism/components/prism-javascript.min.js"))

            # Plotly local-first, CDN-fallback
            head.add(raw_util(
                f"<script src=\"{rel_prefix}assets/vendor/plotly/plotly.min.js\" "
                "onerror=\"var s=document.createElement('script');"
                "s.src='https://cdn.plot.ly/plotly-2.32.0.min.js';"
                "document.head.appendChild(s);\"></script>"
            ))

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


class Directory:
    """
    A Directory aggregates multiple Dashboard instances and publishes them
    as a landing page listing multiple dashboards. Each dashboard is published
    into its own subfolder under the output directory.
    """
    
    def __init__(self, title="Dashboard Directory", page_width=900):
        """
        Initialize a Directory.
        
        Args:
            title (str): The title of the directory landing page
            page_width (int): The default page width for the landing page
        """
        self.title = title
        self.page_width = page_width
        self.dashboards = []  # List of (slug, dashboard) tuples
    
    def add_dashboard(self, dashboard, slug=None):
        """
        Add a Dashboard instance to the directory.
        
        Args:
            dashboard (Dashboard): The Dashboard instance to add
            slug (str, optional): URL-friendly identifier for the dashboard.
                                 If None, derived from dashboard title.
        """
        if slug is None:
            # Generate slug from dashboard title
            slug = dashboard.title.lower().replace(" ", "-")
            # Remove special characters
            slug = "".join(c for c in slug if c.isalnum() or c == "-")
            # Clean up multiple consecutive hyphens
            slug = re.sub(r'-+', '-', slug)
            # Remove leading/trailing hyphens
            slug = slug.strip("-")
        
        self.dashboards.append((slug, dashboard))
    
    def publish(self, output_dir="output"):
        """
        Publish the directory landing page and all dashboards.
        
        Creates a landing page (index.html) that links to each dashboard,
        and publishes each dashboard into its own subfolder.
        
        Args:
            output_dir (str): The output directory path
        """
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # Copy assets to the root output directory
        assets_src = os.path.join(os.path.dirname(__file__), "assets")
        assets_dst = os.path.join(output_dir, "assets")
        shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
        
        # Publish each dashboard to its own subfolder
        for slug, dashboard in self.dashboards:
            dashboard_dir = os.path.join(output_dir, slug)
            dashboard.publish(output_dir=dashboard_dir)
            
            # Add a "Back to Directory" link to each dashboard's index page
            self._add_back_link(dashboard_dir, slug)
        
        # Create the landing page
        self._create_landing_page(output_dir)
    
    def _add_back_link(self, dashboard_dir, slug):
        """
        Add a navigation link back to the directory landing page in the dashboard.
        
        Args:
            dashboard_dir (str): Path to the dashboard output directory
            slug (str): The slug of the dashboard
        """
        index_path = os.path.join(dashboard_dir, "index.html")
        if not os.path.exists(index_path):
            return
        
        # Read the existing index.html
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add a back link in the sidebar footer
        # Replace the sidebar-footer section with one that includes a back link
        back_link = '<div id="sidebar-footer"><a href="../index.html">← Back to Directory</a></div>'
        
        # Find and replace the sidebar-footer
        pattern = r'<div id="sidebar-footer">.*?</div>'
        content = re.sub(pattern, back_link, content, flags=re.DOTALL)
        
        # Write back the modified content
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Also update all page HTML files to have the back link
        pages_dir = os.path.join(dashboard_dir, "pages")
        if os.path.exists(pages_dir):
            for page_file in os.listdir(pages_dir):
                if page_file.endswith(".html"):
                    page_path = os.path.join(pages_dir, page_file)
                    with open(page_path, "r", encoding="utf-8") as f:
                        page_content = f.read()
                    
                    # For pages, the back link needs to go up two levels
                    back_link_pages = '<div id="sidebar-footer"><a href="../../index.html">← Back to Directory</a></div>'
                    page_content = re.sub(pattern, back_link_pages, page_content, flags=re.DOTALL)
                    
                    with open(page_path, "w", encoding="utf-8") as f:
                        f.write(page_content)
    
    def _create_landing_page(self, output_dir):
        """
        Create the landing page HTML that lists all dashboards.
        
        Args:
            output_dir (str): Path to the output directory
        """
        doc = document(title=self.title)
        
        # Add CSS and basic styling
        with doc.head:
            # Ensure charset is declared for the landing page too
            doc.head.add(raw_util('<meta charset="utf-8" />'))
            link(rel="stylesheet", href="assets/css/style.css")
            raw_util("""
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }
                .directory-container {
                    max-width: """ + str(self.page_width) + """px;
                    margin: 0 auto;
                    padding: 40px 20px;
                }
                .directory-header {
                    text-align: center;
                    margin-bottom: 50px;
                }
                .directory-header h1 {
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    color: #333;
                }
                .directory-header p {
                    font-size: 1.2em;
                    color: #666;
                }
                .dashboard-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 30px;
                    margin-top: 30px;
                }
                .dashboard-card {
                    background: white;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    transition: transform 0.2s, box-shadow 0.2s;
                    text-decoration: none;
                    color: inherit;
                    display: block;
                }
                .dashboard-card:hover {
                    transform: translateY(-4px);
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
                }
                .dashboard-card h2 {
                    margin: 0 0 10px 0;
                    font-size: 1.5em;
                    color: #2c3e50;
                }
                .dashboard-card p {
                    margin: 0;
                    color: #7f8c8d;
                    font-size: 0.95em;
                }
                .dashboard-arrow {
                    display: inline-block;
                    margin-left: 5px;
                    transition: transform 0.2s;
                }
                .dashboard-card:hover .dashboard-arrow {
                    transform: translateX(5px);
                }
                .footer {
                    text-align: center;
                    margin-top: 60px;
                    padding: 20px;
                    color: #999;
                    font-size: 0.9em;
                }
            </style>
            """)
        
        with doc:
            with div(cls="directory-container"):
                with div(cls="directory-header"):
                    h1(self.title)
                    p(f"Explore {len(self.dashboards)} dashboard{'s' if len(self.dashboards) != 1 else ''}")
                
                with div(cls="dashboard-grid"):
                    for slug, dashboard in self.dashboards:
                        with a(href=f"{slug}/index.html", cls="dashboard-card"):
                            h2(dashboard.title)
                            num_pages = len(dashboard.pages)
                            p(f"{num_pages} page{'s' if num_pages != 1 else ''} ")
                            span("→", cls="dashboard-arrow")
                
                with div(cls="footer"):
                    p("Produced by staticdash")
        
        # Write the landing page
        with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(str(doc))
