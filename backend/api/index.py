"""Vercel serverless entry point — imports the demo server FastAPI app."""
import os
import sys

_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _path not in sys.path:
    sys.path.insert(0, _path)

from _demo_server import app
