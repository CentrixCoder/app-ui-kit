"""The Flask helper, for Python apps without Dash."""

from __future__ import annotations

from flask import Flask, render_template_string

import app_ui_kit
from app_ui_kit.flask import init_app


def test_a_flask_app_serves_the_files_and_renders_the_tags():
    app = Flask(__name__)
    init_app(app)
    init_app(app)  # twice is harmless

    @app.route("/")
    def index():
        return render_template_string("<head>{{ app_ui_kit_head() }}</head><body>{{ app_ui_kit_scripts() }}</body>")

    client = app.test_client()
    page = client.get("/").get_data(as_text=True)
    css_url = app_ui_kit.versioned_url("app-ui-kit.css")
    js_url = app_ui_kit.versioned_url("app-ui-kit.js")
    assert f'<link rel="stylesheet" href="{css_url}">' in page
    assert f'<script src="{js_url}"></script>' in page
    assert client.get(css_url).status_code == 200
    assert client.get(js_url).status_code == 200
