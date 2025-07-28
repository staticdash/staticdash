# Import everything you want to expose at the package level
from .dashboard import Dashboard, MiniPage, Page

# Optionally, define __all__ to control what gets imported with `from staticdash import *`
__all__ = ["Dashboard", "MiniPage", "Page"]

# Automatically check for Chrome when imported
try:
    from ._postinstall import ensure_chrome
    ensure_chrome()
except Exception:
    pass
