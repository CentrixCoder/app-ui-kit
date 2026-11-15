"""
app_ui_kit.flask: serve the kit's CSS and JS from any Flask app.

    from flask import Flask
    from app_ui_kit.flask import init_app

    app = Flask(__name__)
    init_app(app)          # serves /_app-ui-kit/<version>-<hash>/app-ui-kit.css and .js

Then put ``{{ app_ui_kit_head() }}`` in <head> (after Bootstrap, before the
app's own CSS) and ``{{ app_ui_kit_scripts() }}`` at the end of <body>.
Dash apps call ``app_ui_kit.dash.use(app)`` instead, which uses this.
"""

from __future__ import annotations

from markupsafe import Markup

from app_ui_kit import SCRIPT, STYLESHEET, URL_PREFIX, fingerprint, static_dir, versioned_url

_ENDPOINT = "app_ui_kit_static"


def init_app(flask_app, prefix: str = "") -> None:
    """Register the static route and the two Jinja helpers on ``flask_app``.

    ``prefix`` is any path the app is mounted under (Dash's
    ``routes_pathname_prefix``); the route is ``<prefix>/_app-ui-kit/<version>/<file>``.
    Safe to call twice.
    """
    if _ENDPOINT in flask_app.view_functions:
        return

    from flask import abort, send_from_directory

    rule = f"{prefix.rstrip('/')}{URL_PREFIX}/<version>/<path:name>"

    def serve(version: str, name: str):
        # Only the two shipped files, and only their current fingerprint: anything else is a 404.
        if version != fingerprint() or name not in (STYLESHEET, SCRIPT):
            abort(404)
        response = send_from_directory(static_dir(), name, max_age=31536000)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    flask_app.add_url_rule(rule, endpoint=_ENDPOINT, view_func=serve)

    if hasattr(flask_app, "jinja_env"):
        flask_app.jinja_env.globals["app_ui_kit_head"] = lambda: head_tags(prefix)
        flask_app.jinja_env.globals["app_ui_kit_scripts"] = lambda: script_tags(prefix)


def head_tags(prefix: str = "") -> Markup:
    """``<link>`` tag for the stylesheet."""
    return Markup(f'<link rel="stylesheet" href="{versioned_url(STYLESHEET, prefix)}">')


def script_tags(prefix: str = "") -> Markup:
    """``<script>`` tag for the behaviour file."""
    return Markup(f'<script src="{versioned_url(SCRIPT, prefix)}"></script>')
