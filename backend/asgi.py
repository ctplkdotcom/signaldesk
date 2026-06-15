"""ASGI entry point for PythonAnywhere."""
import os
import sys

_path = os.path.dirname(os.path.abspath(__file__))
if _path not in sys.path:
    sys.path.insert(0, _path)

# Let config.py and the demo server read env vars from PythonAnywhere's
# "Web" tab environment variable section — no .env file needed here.

from _demo_server import app as application
