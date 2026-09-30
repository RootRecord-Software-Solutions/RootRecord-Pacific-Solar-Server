"""Context session store. Importing this package does not open a port."""

from .store import DEFAULT_ROOT, SessionStore

__all__ = ["DEFAULT_ROOT", "SessionStore", "create_app"]


def create_app(root=None):
    """Load the FastAPI factory only when called. This package does not serve it."""
    from .api import create_app as _create_app

    return _create_app(root)
