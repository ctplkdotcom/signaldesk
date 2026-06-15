"""ASGI entry point for PythonAnywhere.

Uses the demo server (no DB needed) by default.
Set USE_REAL_APP=true env var to use the real database-backed app.
"""
import os
import sys

_path = os.path.dirname(os.path.abspath(__file__))
if _path not in sys.path:
    sys.path.insert(0, _path)

use_real_app = os.getenv("USE_REAL_APP", "").lower() in ("true", "1", "yes")

if use_real_app:
    from app.main import app as application
else:
    from _demo_server import app as application
