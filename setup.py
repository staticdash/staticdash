# setup.py
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from pathlib import Path
import os
import shutil
import urllib.request

# Where your repo assets live
REPO_ASSETS = Path("staticdash/assets")
VENDOR_DIR = REPO_ASSETS / "vendor"

# Simple cache dir (respects XDG if set)
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "staticdash"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# If you need to force “no network” builds in CI:
#   STATICDASH_VENDOR_OFFLINE=1  -> require the files to already be in the cache
OFFLINE = os.environ.get("STATICDASH_VENDOR_OFFLINE", "0") == "1"

# (relative path under vendor, url)
VENDOR_FILES = [
    ("plotly/plotly.min.js", "https://cdn.plot.ly/plotly-2.32.0.min.js"),
    ("mathjax/tex-mml-chtml.js", "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"),
    ("prism/prism-tomorrow.min.css", "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-tomorrow.min.css"),
    ("prism/prism.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"),
    ("prism/components/prism-python.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-python.min.js"),
    ("prism/components/prism-javascript.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-javascript.min.js"),
    ("prism/components/prism-sql.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-sql.min.js"),
    ("prism/components/prism-markup.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-markup.min.js"),
    ("prism/components/prism-bash.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-bash.min.js"),
    ("prism/components/prism-json.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-json.min.js"),
    ("prism/components/prism-c.min.js", "https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-c.min.js"),
]

def _cache_path(rel: str) -> Path:
    return CACHE_DIR / rel

def _ensure_file(rel: str, url: str) -> Path:
    """
    Return a path to the cached file; download if missing (unless OFFLINE).
    """
    cpath = _cache_path(rel)
    if cpath.exists():
        return cpath
    if OFFLINE:
        raise RuntimeError(f"[staticdash] Missing cached asset (offline): {cpath}")
    cpath.parent.mkdir(parents=True, exist_ok=True)
    print(f"[staticdash] caching {url} -> {cpath}")
    urllib.request.urlretrieve(url, cpath)
    return cpath

def _vendorize():
    """
    Populate staticdash/assets/vendor/ from the cache (downloading if needed).
    Also ensure css/js folders exist (no changes to your actual code).
    """
    # Make sure base asset dirs exist in the repo (harmless if already present)
    (REPO_ASSETS / "css").mkdir(parents=True, exist_ok=True)
    (REPO_ASSETS / "js").mkdir(parents=True, exist_ok=True)
    # (no content changes to your css/js; we just avoid build errors if missing)

    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    for rel, url in VENDOR_FILES:
        src = _ensure_file(rel, url)
        dst = VENDOR_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Copy into the repo’s vendor directory so setuptools can package it
        if not dst.exists():
            shutil.copy2(src, dst)

class build_py(_build_py):
    def run(self):
        _vendorize()
        super().run()

setup(cmdclass={"build_py": build_py})
