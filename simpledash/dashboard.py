import os
import shutil
from dominate import document
from dominate.tags import div, h1, h2, p, a, script, link
from dominate.util import raw

class Page:
    def __init__(self, slug, title, description=None):
        self.slug = slug
        self.title = title
        self.description = description
        self.content = []

    def append_element(self, element):
        self.content.append(element)

class Dashboard:
    def __init__(self, title="Dashboard"):
        self.title = title
        self.pages = []

    def add_page(self, page):
        self.pages.append(page)

    def publish(self, output_dir="site"):
        os.makedirs(output_dir, exist_ok=True)
        self._write_assets(output_dir)
        self._write_index(output_dir)

    def _write_assets(self, output_dir):
        css_src = os.path.join(os.path.dirname(__file__), "assets", "css", "style.css")
        css_dst_dir = os.path.join(output_dir, "assets", "css")
        os.makedirs(css_dst_dir, exist_ok=True)
        shutil.copyfile(css_src, os.path.join(css_dst_dir, "style.css"))

    def _write_index(self, output_dir):
        doc = document(title=self.title)

        with doc.head:
            link(rel="stylesheet", href="assets/css/style.css")
            s = script(type="text/javascript")
            s.add(raw("""
function showPage(id) {
  document.querySelectorAll('.page-section').forEach(el => el.style.display = 'none');
  document.getElementById(id).style.display = 'block';
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
  event.target.classList.add('active');
}
window.onload = () => showPage('page-0');
"""))

        with doc:
            with div(id="sidebar"):
                h1(self.title)
                for i, page in enumerate(self.pages):
                    a(page.title, href="#", cls="nav-link", onclick=f"showPage('page-{i}')")
            with div(id="content"):
                for i, page in enumerate(self.pages):
                    with div(id=f"page-{i}", cls="page-section"):
                        h2(page.title)
                        if page.description:
                            p(page.description)
                        for element in page.content:
                            doc.body.add(raw(str(element)))

        with open(os.path.join(output_dir, "index.html"), "w") as f:
            f.write(doc.render())