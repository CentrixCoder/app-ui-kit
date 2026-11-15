"""
app-ui-kit: the shared look of every app in the family.

The styling lives in two files shipped inside this package:

    static/app-ui-kit.css   tokens, page frame, controls (the one copy)
    static/app-ui-kit.js    theme, one-open-step, Auto-run gate, Plotly sizing

How an app loads them:

    Dash        from app_ui_kit import dash as ui; ui.use(app)
    Flask       from app_ui_kit.flask import init_app; init_app(flask_app)
    npm         import "app-ui-kit/app-ui-kit.css"
    plain HTML  copy nothing: serve the files with one of the above, or see README

Version: one number, here. pyproject.toml reads it; package.json and
app-ui-kit.js must match it (tests/test_package.py fails when they drift).
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

__version__ = "0.1.1"

STYLESHEET = "app-ui-kit.css"
SCRIPT = "app-ui-kit.js"

#: URL path the Python helpers serve the files under, followed by ``fingerprint()``
#: so changed files are never served from a browser's cache of the old ones.
URL_PREFIX = "/_app-ui-kit"


def static_dir() -> Path:
    """The folder holding app-ui-kit.css and app-ui-kit.js."""
    return Path(__file__).resolve().parent / "static"


def static_path(name: str) -> Path:
    """Absolute path of one shipped file (``STYLESHEET`` or ``SCRIPT``)."""
    if name not in (STYLESHEET, SCRIPT):
        raise ValueError(f"app-ui-kit ships {STYLESHEET!r} and {SCRIPT!r}, not {name!r}")
    return static_dir() / name


@lru_cache(maxsize=1)
def fingerprint() -> str:
    """``<version>-<hash>``: the version plus a hash of both files' content.

    The files are served with a one-year cache, so the URL must change whenever
    their content does -- including edits made without a version bump (an
    editable install while the kit itself is being changed).
    """
    digest = hashlib.sha256()
    for name in (STYLESHEET, SCRIPT):
        digest.update(static_path(name).read_bytes())
    return f"{__version__}-{digest.hexdigest()[:10]}"


def versioned_url(name: str, prefix: str = "") -> str:
    """The URL the Python helpers serve ``name`` at, e.g. ``/_app-ui-kit/0.1.0-3f2a9c1b04/app-ui-kit.css``."""
    static_path(name)  # validates the name
    return f"{prefix.rstrip('/')}{URL_PREFIX}/{fingerprint()}/{name}"


__all__ = ["__version__", "STYLESHEET", "SCRIPT", "URL_PREFIX", "static_dir", "static_path", "fingerprint",
           "versioned_url"]
