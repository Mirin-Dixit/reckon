"""Test package import."""


def test_app_import():
    """Verify that the app package can be imported."""
    import app

    assert app is not None
