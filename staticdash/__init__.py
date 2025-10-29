# Import everything you want to expose at the package level
from .dashboard import Dashboard, MiniPage, Page, Directory

# Optionally, define __all__ to control what gets imported with `from staticdash import *`
__all__ = ["Dashboard", "MiniPage", "Page", "Directory"]