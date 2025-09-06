# tests/test_server.py

import sys
from pathlib import Path

# Add the 'src' directory to the Python path so we can import our code
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Now we can import the function we want to test
from src.mcp_server import resolve_path

# A test function must start with 'test_'
def test_resolve_path_alias():
    """
    Tests if the resolve_path function correctly converts
    a common alias like 'desktop' to the full, correct path.
    """
    # Get the expected path to the Desktop folder
    expected_path = Path.home() / "Desktop"

    # Call the function from your server code
    actual_path = resolve_path("desktop")

    # Assert that the function's output matches what we expect
    assert actual_path == expected_path