"""Test USDAssemble."""

import usdassemble


def test_import() -> None:
    """Test that the app can be imported."""
    assert isinstance(usdassemble.__name__, str)
