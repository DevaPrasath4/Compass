import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_backend_imports_cleanly():
    import main
    assert main.app.title == "Compass API"
