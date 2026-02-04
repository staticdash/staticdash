import os
import shutil
import uuid
import re
from typing import Optional, Tuple, List, Any
import pandas as pd
import plotly.graph_objects as go
from dominate import document
from dominate.tags import div, h1, h2, h3, h4, p, a, script, link, span, ul, li
from dominate.util import raw as raw_util
import html
import io
import base64
import matplotlib
from matplotlib import rc_context
import json
import markdown

# Constants
DEFAULT_PAGE_WIDTH = 900
DEFAULT_SIDEBAR_WIDTH = 240
DEFAULT_CONTENT_PADDING = 20
HEADER_TAGS = {1: h1, 2: h2, 3: h3, 4: h4}
VALID_ALIGNMENTS = {"left", "center", "right"}
DEFAULT_FONT_FAMILY = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'


def render_markdown_text(text):
    """
    Render markdown text to HTML, preserving math expressions.
    
    Math expressions in $...$ (inline) or $$...$$ (display) format are
    protected during markdown processing and passed through for MathJax.
    """
    math_blocks = []
    
    def replace_math(match):
        math_blocks.append(match.group(0))
        # Use a placeholder that won't be affected by markdown processing
        return f"STATICDASHMATH{len(math_blocks)-1}ENDMATH"
    
    # Protect math expressions from markdown processing
    text = re.sub(r'\$\$([^$]+)\$\$', replace_math, text, flags=re.DOTALL)
    text = re.sub(r'\$([^$]+)\$', replace_math, text, flags=re.DOTALL)
    
    # Process markdown with extended features
    md = markdown.Markdown(extensions=[
        'extra',           # Tables, fenced code blocks, etc.
        'nl2br',           # Convert newlines to <br>
        'sane_lists',      # Better list handling
        'pymdownx.tilde',  # Strikethrough with ~~text~~
        'pymdownx.superfences',  # Better code blocks with custom fence support
    ], extension_configs={
        'pymdownx.superfences': {
            'custom_fences': [
                {
                    'name': 'mermaid',
                    'class': 'mermaid',
                    'format': lambda source, language, css_class, options, md, **kwargs: 
                        f'<div class="mermaid">\n{source}\n</div>'
                }
            ]
        }
    })
    html_content = md.convert(text)
    
    # Restore math expressions
    for i, block in enumerate(math_blocks):
        html_content = html_content.replace(f"STATICDASHMATH{i}ENDMATH", block)
    
    return html_content


def split_paragraphs_preserving_math(text):
    """
    Split text into paragraphs on double newlines, preserving math expressions.
    Assumes math is in $...$ (inline) or $$...$$ (display) format.
    """
    math_blocks = []
    
    def replace_math(match):
        math_blocks.append(match.group(0))
        return f"__MATH_BLOCK_{len(math_blocks)-1}__"
    
    # Handle display math first ($$...$$), then inline ($...$)
    text = re.sub(r'\$\$([^$]+)\$\$', replace_math, text, flags=re.DOTALL)
    text = re.sub(r'\$([^$]+)\$', replace_math, text, flags=re.DOTALL)
    
    # Split on double newlines and restore math
    paragraphs = []
    for para in text.split('\n\n'):
        for i, block in enumerate(math_blocks):
            para = para.replace(f"__MATH_BLOCK_{i}__", block)
        if para.strip():
            paragraphs.append(para.strip())
    
    return paragraphs


def get_alignment_style(align: str) -> str:
    """Generate CSS flexbox alignment style."""
    align = align if align in VALID_ALIGNMENTS else "center"
    justify_map = {"center": "center", "left": "flex-start", "right": "flex-end"}
    return f"display:flex; justify-content:{justify_map[align]}; align-items:center;"


def extract_plot_params(content: Any) -> Tuple[Any, Optional[int], Optional[int], str]:
    """Extract figure, height, width, and alignment from plot content tuple."""
    if not isinstance(content, (list, tuple)):
        return content, None, None, "center"
    
    if len(content) == 4:
        return content
    elif len(content) == 3:
        return (*content, "center")
    elif len(content) == 2:
        return (*content, None, "center")
    else:
        return content[0], None, None, "center"


def get_figure_layout_attr(fig, attr: str, default=None):
    """Safely get a layout attribute from a figure."""
    try:
        return getattr(getattr(fig, 'layout', None), attr, default)
    except Exception:
        return default


def set_figure_dimensions(fig, height: Optional[int], width: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
    """Set figure dimensions and return original values."""
    orig_height = get_figure_layout_attr(fig, 'height')
    orig_width = get_figure_layout_attr(fig, 'width')
    
    try:
        if height is not None:
            fig.update_layout(height=height)
        if width is not None:
            fig.update_layout(width=width)
    except Exception:
        pass
    
    return orig_height, orig_width


def restore_figure_dimensions(fig, orig_height: Optional[int], orig_width: Optional[int]):
    """Restore original figure dimensions."""
    try:
        if orig_height is not None or orig_width is not None:
            fig.update_layout(height=orig_height, width=orig_width)
    except Exception:
        pass


def ensure_figure_font(fig):
    """Ensure figure has a robust font family."""
    try:
        font_family = get_figure_layout_attr(fig, 'font.family')
        if not font_family:
            fig.update_layout(font_family=DEFAULT_FONT_FAMILY)
    except Exception:
        pass


def build_container_style(width: Optional[int] = None, height: Optional[int] = None) -> str:
    """Build container style string for plots."""
    style = "width:100%;" if width is None else f"width:{width}px;"
    if height is not None:
        style += f" height:{height}px;"
    return style


def render_plotly_figure(fig, specified_height: Optional[int], specified_width: Optional[int], specified_align: str) -> str:
    """Render a Plotly figure to HTML with deferred loading."""
    ensure_figure_font(fig)
    orig_height, orig_width = set_figure_dimensions(fig, specified_height, specified_width)
    
    try:
        fig_json = fig.to_json()
        fig_json = fig_json.replace('</script>', '<\\/script>')
        div_id = f'plot-{uuid.uuid4()}'
        container_style = build_container_style(specified_width, specified_height)
        
        plot_div = f'<div id="{div_id}" class="plotly-graph-div" style="{container_style}"></div>'
        loader = (
            '<script type="text/javascript">(function(){'
            f'var fig = {fig_json};'
            'function tryPlot(){'
            'if(window.Plotly && typeof window.Plotly.newPlot === "function"){'
            f'Plotly.newPlot("{div_id}", fig.data, fig.layout, {json.dumps({"responsive": True})});'
            '} else { setTimeout(tryPlot, 50); }'
            '}'
            'if(document.readyState === "complete"){ tryPlot(); } else { window.addEventListener("load", tryPlot); }'
            '})();</script>'
        )
        plot_wrapped = plot_div + loader
    except Exception:
        # Fallback to older method
        plotly_html = fig.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True})
        container_style = build_container_style(specified_width, specified_height)
        plot_wrapped = f'<div style="{container_style}">{plotly_html}</div>'
    finally:
        restore_figure_dimensions(fig, orig_height, orig_width)
    
    align_style = get_alignment_style(specified_align)
    return f'<div style="{align_style}">{plot_wrapped}</div>'


def render_matplotlib_figure(fig, specified_height: Optional[int], specified_width: Optional[int], specified_align: str) -> str:
    """Render a Matplotlib figure to base64 PNG."""
    buf = io.BytesIO()
    try:
        # Adjust figure size if dimensions specified
        orig_size = None
        try:
            dpi = fig.get_dpi()
            if dpi and (specified_height or specified_width):
                orig_size = fig.get_size_inches()
                new_w, new_h = orig_size
                if specified_width:
                    new_w = specified_width / dpi
                if specified_height:
                    new_h = specified_height / dpi
                fig.set_size_inches(new_w, new_h)
        except Exception:
            pass
        
        with rc_context({"axes.unicode_minus": False}):
            fig.savefig(buf, format="png", bbox_inches="tight")
        
        # Restore original size
        if orig_size is not None:
            try:
                fig.set_size_inches(orig_size)
            except Exception:
                pass
        
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        
        img_style = "max-width:100%;"
        if specified_height:
            img_style += f" height:{specified_height}px;"
        if specified_width:
            img_style += f" width:{specified_width}px;"
        
        align_style = get_alignment_style(specified_align)
        return f'<div style="{align_style}"><img src="data:image/png;base64,{img_base64}" style="{img_style}"></div>'
    except Exception as e:
        return f'<div>Matplotlib figure could not be rendered: {e}</div>'
    finally:
        buf.close()


class AbstractPage:
    def __init__(self):
        self.elements = []

    def add_header(self, text, level=1, width=None):
        if level not in (1, 2, 3, 4):
            raise ValueError("Header level must be 1, 2, 3, or 4")
        self.elements.append(("header", (text, level), width))

    def add_text(self, text, width=None):
        self.elements.append(("text", text, width))

    def add_plot(self, plot, el_width=None, height=None, width=None, align="center"):
        self.elements.append(("plot", (plot, height, width, align), el_width))

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

    def _render_element(self, kind, content, index=None, downloads_dir=None, 
                       relative_prefix="", inherited_width=None, 
                       inherited_marking=None, inherited_distribution=None):
        """Common element rendering logic shared by Page and MiniPage."""
        if kind == "text":
            # Render markdown to HTML
            html_content = render_markdown_text(content)
            return div(raw_util(html_content))
        
        elif kind == "header":
            text, level = content
            return HEADER_TAGS[level](text)
        
        elif kind == "plot":
            fig, specified_height, specified_width, specified_align = extract_plot_params(content)
            
            if hasattr(fig, "to_html"):
                html_content = render_plotly_figure(fig, specified_height, specified_width, specified_align)
            else:
                html_content = render_matplotlib_figure(fig, specified_height, specified_width, specified_align)
            
            return div(raw_util(html_content))
        
        elif kind == "table":
            df = content
            try:
                html_table = df.to_html(
                    classes="table-hover table-striped",
                    index=False,
                    border=0,
                    table_id=f"table-{index}" if index else None,
                    escape=False
                )
                return div(raw_util(html_table))
            except Exception as e:
                return div(f"Table could not be rendered: {e}")
        
        elif kind == "download":
            file_path, label = content
            btn = a(label or os.path.basename(file_path), href=file_path, 
                   cls="download-button", download=True)
            return div(btn)
        
        elif kind == "syntax":
            code, language = content
            return div(
                raw_util(f'<pre class="syntax-block"><code class="language-{language}">{html.escape(code)}</code></pre>'),
                cls="syntax-block"
            )
        
        elif kind == "minipage":
            return content.render(
                index,
                downloads_dir=downloads_dir,
                relative_prefix=relative_prefix,
                inherited_width=inherited_width,
                inherited_marking=inherited_marking,
                inherited_distribution=inherited_distribution
            )
        
        return div("Unknown element type")


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

    def _render_marking_bars(self, effective_marking, effective_distribution):
        """Render top and bottom marking bars."""
        if not effective_marking:
            return []
        
        shared_pos = (
            "position: fixed; "
            f"left: calc(var(--sidebar-width, {DEFAULT_SIDEBAR_WIDTH}px) + var(--content-padding-x, {DEFAULT_CONTENT_PADDING}px)); "
            f"width: calc(100vw - var(--sidebar-width, {DEFAULT_SIDEBAR_WIDTH}px) - 2*var(--content-padding-x, {DEFAULT_CONTENT_PADDING}px)); "
            "text-align: center; background-color: #f8f9fa; padding: 10px; "
            "z-index: 1000; font-weight: normal;"
        )
        
        elements = [
            div(effective_marking, cls="floating-header", style=f"{shared_pos} top: 0;")
        ]
        
        footer_content = []
        if effective_distribution:
            footer_content.append(div(effective_distribution, style="margin-bottom: 4px; font-size: 10pt;"))
        footer_content.append(div(effective_marking))
        
        elements.append(
            div(*footer_content, cls="floating-footer", style=f"{shared_pos} bottom: 0;")
        )
        
        return elements

    def render(self, index, downloads_dir=None, relative_prefix="",
               inherited_width=None, inherited_marking=None, inherited_distribution=None):
        effective_width = self.page_width or inherited_width or DEFAULT_PAGE_WIDTH
        effective_marking = self.marking if self.marking is not None else inherited_marking
        effective_distribution = getattr(self, "distribution", None) or inherited_distribution

        elements = self._render_marking_bars(effective_marking, effective_distribution)

        # Render all page elements
        for kind, content, el_width in self.elements:
            elem = self._render_element(
                kind, content, index, downloads_dir, relative_prefix,
                effective_width, effective_marking, effective_distribution
            )
            
            if el_width is not None:
                elem = div(elem, style=f"width: {el_width * 100}%;")
                elem = div(elem, style="display: flex; justify-content: center; margin: 0 auto;")
            
            elements.append(elem)

        wrapper_style = (
            f"max-width: {effective_width}px; margin: 0 auto; width: 100%; "
            f"padding-top: 80px; padding-bottom: 80px; --content-width: {effective_width}px;"
        )
        return [div(*elements, style=wrapper_style)]


class MiniPage(AbstractPage):
    def __init__(self, page_width=None):
        super().__init__()
        self.page_width = page_width

    def render(self, index=None, downloads_dir=None, relative_prefix="",
               inherited_width=None, inherited_marking=None, inherited_distribution=None):
        effective_width = self.page_width or inherited_width or DEFAULT_PAGE_WIDTH
        row_div = div(
            cls="minipage-row",
            style=f"max-width: {effective_width}px; margin: 0 auto; width: 100%;"
        )
        
        for kind, content, el_width in self.elements:
            elem = self._render_element(
                kind, content, index, downloads_dir, relative_prefix,
                effective_width, inherited_marking, inherited_distribution
            )
            
            if el_width is not None:
                elem = div(elem, style=f"width: {el_width * 100}%;")
                elem = div(elem, style="display: flex; justify-content: center; margin: 0 auto;")
            
            row_div += div(elem, cls="minipage-cell")
        
        return row_div


class Dashboard:
    def __init__(self, title="Dashboard", page_width=DEFAULT_PAGE_WIDTH, marking=None, distribution=None):
        self.title = title
        self.pages = []
        self.page_width = page_width
        self.marking = marking            # Dashboard-wide default (None => no marking)
        self.distribution = distribution  # Dashboard-wide distribution statement

    def add_page(self, page):
        self.pages.append(page)

    def _has_active_child(self, page, current_slug):
        """Check if page has an active child recursively."""
        return any(
            child.slug == current_slug or self._has_active_child(child, current_slug)
            for child in getattr(page, "children", [])
        )

    def _get_page_href(self, page, prefix="", is_first_page=False, viewing_from_index=False):
        """
        Get the href for a page, handling first page as index.html.
        
        Args:
            page: The page to link to
            prefix: The prefix for non-first pages ("pages/" or "")
            is_first_page: Whether this is the first page (becomes index.html)
            viewing_from_index: Whether we're viewing from index.html (vs pages/*.html)
        """
        if is_first_page:
            # First page is always index.html
            if viewing_from_index:
                return "index.html"
            else:
                return "../index.html"
        else:
            return f"{prefix}{page.slug}.html"

    def _render_sidebar(self, pages, prefix="", current_slug=None, viewing_from_index=False, is_top_level=True):
        """Render sidebar navigation."""
        for i, page in enumerate(pages):
            # Only the first top-level page becomes index.html
            is_first_page = (i == 0 and is_top_level)
            page_href = self._get_page_href(page, prefix, is_first_page, viewing_from_index)
            is_active = (page.slug == current_slug)
            has_children = bool(getattr(page, "children", []))
            group_open = self._has_active_child(page, current_slug)

            link_classes = "nav-link"
            if has_children:
                link_classes += " sidebar-parent"
            if is_active:
                link_classes += " active"

            if has_children:
                group_cls = "sidebar-group open" if (group_open or is_active) else "sidebar-group"
                with div(cls=group_cls):
                    a([span("", cls="sidebar-arrow"), page.title], cls=link_classes, href=page_href)
                    with div(cls="sidebar-children"):
                        # Children are not top-level, so they won't be treated as index.html
                        self._render_sidebar(page.children, prefix, current_slug, viewing_from_index, is_top_level=False)
            else:
                a(page.title, cls="nav-link", href=page_href)

    def _add_head_assets(self, head, rel_prefix, effective_width):
        """Add CSS, JavaScript, and other assets to document head."""
        head.add(raw_util('<meta charset="utf-8" />'))
        head.add(raw_util('<meta name="viewport" content="width=device-width, initial-scale=1" />'))
        head.add(link(rel="stylesheet", href=f"{rel_prefix}assets/css/style.css"))
        head.add(script(type="text/javascript", src=f"{rel_prefix}assets/js/script.js"))

        # MathJax config
        head.add(raw_util(
            "<script>window.MathJax={tex:{inlineMath:[['$','$'],['\\\\(','\\\\)']],displayMath:[['$$','$$'],['\\\\[','\\\\]']]}};</script>"
        ))
        head.add(raw_util(
            f'<script src="{rel_prefix}assets/vendor/mathjax/tex-svg.js" '
            'onerror="var s=document.createElement(\'script\');'
            's.src=\'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js\';'
            'document.head.appendChild(s);"></script>'
        ))

        # Prism syntax highlighting
        head.add(link(rel="stylesheet", href=f"{rel_prefix}assets/vendor/prism/prism-tomorrow.min.css"))
        head.add(script(src=f"{rel_prefix}assets/vendor/prism/prism.min.js"))
        head.add(script(src=f"{rel_prefix}assets/vendor/prism/components/prism-python.min.js"))
        head.add(script(src=f"{rel_prefix}assets/vendor/prism/components/prism-javascript.min.js"))

        # Plotly with CDN fallback
        head.add(raw_util(
            f'<script src="{rel_prefix}assets/vendor/plotly/plotly.min.js" '
            'onerror="var s=document.createElement(\'script\');'
            's.src=\'https://cdn.plot.ly/plotly-2.32.0.min.js\';'
            'document.head.appendChild(s);"></script>'
        ))

        # Mermaid.js for diagrams (local-first, CDN fallback)
        head.add(raw_util(
            f'<script src="{rel_prefix}assets/vendor/mermaid/mermaid.min.js" '
            'onerror="var s=document.createElement(\'script\');'
            's.src=\'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js\';'
            's.onload=function(){{mermaid.initialize({{startOnLoad:true,theme:\'default\'}});}};'
            'document.head.appendChild(s);"></script>'
        ))
        head.add(raw_util(
            '<script>if(typeof mermaid!=="undefined"){mermaid.initialize({ startOnLoad: true, theme: "default" });}</script>'
        ))

        # CSS variables
        head.add(raw_util(
            f"<style>:root{{--sidebar-width:{DEFAULT_SIDEBAR_WIDTH}px;--content-padding-x:{DEFAULT_CONTENT_PADDING}px;}}</style>"
        ))
        head.add(raw_util(f"<style>.content-inner {{ max-width: {effective_width}px !important; }}</style>"))

    def _write_page_html(self, page, output_dir, pages_dir, downloads_dir, rel_prefix="../"):
        """Write a single page HTML file."""
        doc = document(title=page.title)
        effective_width = page.page_width or self.page_width

        with doc.head:
            self._add_head_assets(doc.head, rel_prefix=rel_prefix, effective_width=effective_width)

        with doc:
            with div(id="sidebar"):
                a(self.title, href=f"{rel_prefix}index.html", cls="sidebar-title")
                # When on index.html (rel_prefix=""), other pages are in pages/ directory
                # When on pages/*.html (rel_prefix="../"), other pages are in same directory (no prefix needed)
                viewing_from_index = (rel_prefix == "")
                sidebar_prefix = "pages/" if viewing_from_index else ""
                self._render_sidebar(self.pages, prefix=sidebar_prefix, current_slug=page.slug, 
                                   viewing_from_index=viewing_from_index)
                with div(id="sidebar-footer"):
                    a("Produced by staticdash", href=f"{rel_prefix}index.html" if rel_prefix else "index.html")
            with div(id="content"):
                with div(cls="content-inner"):
                    for el in page.render(
                        0,
                        downloads_dir=downloads_dir,
                        relative_prefix=rel_prefix,
                        inherited_width=self.page_width,
                        inherited_marking=self.marking,
                        inherited_distribution=self.distribution
                    ):
                        div(el)

        # Determine output path: index.html for first page (rel_prefix=""), otherwise pages/{slug}.html
        if rel_prefix == "":
            output_path = os.path.join(output_dir, "index.html")
        else:
            output_path = os.path.join(pages_dir, f"{page.slug}.html")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(str(doc))

    def publish(self, output_dir="output"):
        output_dir = os.path.abspath(output_dir)
        pages_dir = os.path.join(output_dir, "pages")
        downloads_dir = os.path.join(output_dir, "downloads")
        assets_src = os.path.join(os.path.dirname(__file__), "assets")
        assets_dst = os.path.join(output_dir, "assets")

        os.makedirs(pages_dir, exist_ok=True)
        os.makedirs(downloads_dir, exist_ok=True)
        shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)

        def write_page(page, is_first=False):
            # First page goes to index.html, others go to pages/ directory
            if is_first:
                self._write_page_html(page, output_dir, pages_dir, downloads_dir, rel_prefix="")
            else:
                self._write_page_html(page, output_dir, pages_dir, downloads_dir)
            
            # Recursively write children
            for child in getattr(page, "children", []):
                write_page(child, is_first=False)

        # Write all pages
        for i, page in enumerate(self.pages):
            write_page(page, is_first=(i == 0))


class Directory:
    """
    A Directory aggregates multiple Dashboard instances and publishes them
    as a landing page listing multiple dashboards.
    """
    
    def __init__(self, title="Dashboard Directory", page_width=DEFAULT_PAGE_WIDTH):
        self.title = title
        self.page_width = page_width
        self.dashboards = []  # List of (slug, dashboard) tuples
    
    def add_dashboard(self, dashboard, slug=None):
        """Add a Dashboard instance to the directory."""
        if slug is None:
            slug = self._generate_slug(dashboard.title)
        self.dashboards.append((slug, dashboard))
    
    @staticmethod
    def _generate_slug(title):
        """Generate a URL-friendly slug from a title."""
        slug = title.lower().replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        slug = re.sub(r'-+', '-', slug)
        return slug.strip("-")
    
    def _create_landing_page(self, output_dir):
        """Create the landing page HTML that lists all dashboards."""
        doc = document(title=self.title)
        
        with doc.head:
            doc.head.add(raw_util('<meta charset="utf-8" />'))
            link(rel="stylesheet", href="assets/css/style.css")
            raw_util(f"""
            <style>
                body {{
                    font-family: {DEFAULT_FONT_FAMILY};
                    margin: 0; padding: 60px 40px;
                    background-color: #2c3e50;
                    min-height: 100vh;
                }}
                .directory-container {{
                    max-width: {self.page_width}px;
                    margin: 0 auto;
                    background: white;
                    padding: 50px;
                    border-radius: 8px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }}
                .directory-header {{
                    margin-bottom: 40px;
                    border-bottom: 3px solid #16a085;
                    padding-bottom: 20px;
                }}
                .directory-header h1 {{
                    font-size: 2.5em;
                    margin: 0;
                    color: #2c3e50;
                    font-weight: 600;
                }}
                .dashboard-list {{
                    list-style: none;
                    padding: 0;
                    margin: 0;
                }}
                .dashboard-list li {{
                    margin: 0;
                    border-bottom: 1px solid #ecf0f1;
                }}
                .dashboard-list li:last-child {{
                    border-bottom: none;
                }}
                .dashboard-list a {{
                    display: block;
                    padding: 20px 10px;
                    font-weight: 600;
                    font-size: 1.2em;
                    color: #34495e;
                    text-decoration: none;
                    transition: all 0.2s ease;
                }}
                .dashboard-list a:hover {{
                    color: #16a085;
                    padding-left: 20px;
                    background: #f9f9f9;
                }}
            </style>
            """)
        
        with doc:
            with div(cls="directory-container"):
                with div(cls="directory-header"):
                    h1(self.title)
                
                with ul(cls="dashboard-list"):
                    for slug, dashboard in self.dashboards:
                        with li():
                            a(dashboard.title, href=f"{slug}/index.html", target="_blank", rel="noopener noreferrer")
        
        with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(str(doc))
    
    def publish(self, output_dir="output"):
        """Publish the directory landing page and all dashboards."""
        output_dir = os.path.abspath(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        # Copy assets to root
        assets_src = os.path.join(os.path.dirname(__file__), "assets")
        assets_dst = os.path.join(output_dir, "assets")
        shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
        
        # Publish each dashboard independently (no modifications)
        for slug, dashboard in self.dashboards:
            dashboard_dir = os.path.join(output_dir, slug)
            dashboard.publish(output_dir=dashboard_dir)
        
        # Create the directory landing page
        self._create_landing_page(output_dir)
