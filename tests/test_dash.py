"""The Dash helpers: wiring and the frame's structure."""

from __future__ import annotations

import dash_bootstrap_components as dbc
import pytest
from dash import Dash, html

import app_ui_kit
from app_ui_kit import dash as ui

CSS_URL = app_ui_kit.versioned_url("app-ui-kit.css")
JS_URL = app_ui_kit.versioned_url("app-ui-kit.js")


@pytest.fixture
def app(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.css").write_text(":root { --accent: #000; }", encoding="utf-8")
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], assets_folder=str(assets))
    ui.use(app)
    app.layout = html.Div("x")
    return app


def _index(app):
    return app.server.test_client().get("/").get_data(as_text=True)


def test_use_puts_the_kit_after_bootstrap_and_before_the_apps_own_css(app):
    page = _index(app)
    bootstrap, kit, own = page.index(dbc.themes.BOOTSTRAP), page.index(CSS_URL), page.index("app.css")
    assert bootstrap < kit < own


def test_use_adds_the_script(app):
    assert f'src="{JS_URL}"' in _index(app)


def test_the_files_are_served_from_the_package(app):
    client = app.server.test_client()
    css = client.get(CSS_URL)
    assert css.status_code == 200 and "text/css" in css.content_type
    assert css.get_data(as_text=True) == app_ui_kit.static_path("app-ui-kit.css").read_text(encoding="utf-8")
    assert "immutable" in css.headers["Cache-Control"]
    js = client.get(JS_URL)
    assert js.status_code == 200 and "javascript" in js.content_type


def test_other_versions_and_files_are_not_served(app):
    client = app.server.test_client()
    assert client.get("/_app-ui-kit/0.0.0/app-ui-kit.css").status_code == 404
    assert client.get(f"/_app-ui-kit/{app_ui_kit.__version__}/app-ui-kit.css").status_code == 404  # no hash
    assert client.get(f"/_app-ui-kit/{app_ui_kit.fingerprint()}/__init__.py").status_code == 404


def test_use_twice_adds_each_file_once(app):
    ui.use(app)
    assert app.config.external_stylesheets.count(CSS_URL) == 1
    assert app.config.external_scripts.count(JS_URL) == 1


def test_use_honours_a_path_prefix(tmp_path):
    app = Dash(__name__, url_base_pathname="/tool/", assets_folder=str(tmp_path))
    ui.use(app)
    app.layout = html.Div("x")
    url = app_ui_kit.versioned_url("app-ui-kit.css", "/tool/")
    assert url in app.server.test_client().get("/tool/").get_data(as_text=True)
    assert app.server.test_client().get(url).status_code == 200


def _classes(component):
    return (getattr(component, "className", "") or "").split()


def test_page_has_the_frame_in_order():
    page = ui.page(appbar=ui.appbar("app", "Name"), model=ui.model_pane([]), main=ui.results_column([]),
                   statusbar=ui.statusbar(["Not run"]), extra=[html.Div(id="store")])
    assert _classes(page) == ["app"]
    store, appbar, workspace, statusbar = page.children
    assert store.id == "store"
    assert appbar.className == "appbar" and statusbar.className == "statusbar"
    assert _classes(workspace) == ["workspace"]
    assert [c.className for c in workspace.children] == ["model", "main"]


def test_page_without_a_model_pane_is_single_column():
    page = ui.page(appbar=ui.appbar("a"), main=ui.results_column([]), statusbar=ui.statusbar([]))
    workspace = page.children[1]
    assert _classes(workspace) == ["workspace", "workspace--single"]
    assert len(workspace.children) == 1


def test_model_pane_tells_the_css_how_many_steps_it_has():
    steps = [ui.step(i, f"S{i}", [], step_id=f"s{i}") for i in (1, 2, 3)]
    assert ui.model_pane(steps).style == {"--model-steps": "3"}


def test_a_step_keeps_its_body_mounted_and_names_its_summary():
    step = ui.step(2, "Loads", html.Div(id="field"), step_id="loads")
    assert isinstance(step, html.Details) and step.id == "step-loads" and step.open is False
    head, body = step.children
    assert [c.className for c in head.children] == ["step-num", "step-title", "step-sum"]
    assert head.children[2].id == "step-sum-loads"
    assert body.className == "step-body" and body.children.id == "field"


def test_run_tools_has_auto_run_and_the_button():
    checkbox, button = ui.run_tools(run_id="go")
    assert checkbox.id == "chk-auto-run" and checkbox.persistence_type == "local"
    assert button.id == "go" and "run-btn" in _classes(button)
    assert len(ui.run_tools(auto_run_id=None)) == 1


def test_seg_toggle_reports_its_state():
    toggle = ui.seg_toggle("A", "B", id="t")
    assert toggle.className == "seg-toggle"
    assert toggle.to_plotly_json()["props"]["aria-pressed"] == "false"
    assert ui.seg_toggle("A", "B", id="t", pressed=True).to_plotly_json()["props"]["aria-pressed"] == "true"


def test_statusbar_ids_its_first_item_and_pins_the_right_one():
    bar = ui.statusbar(["Not run", "app"], right="note")
    first, second, right = bar.children
    assert first.id == "sb-run" and _classes(second) == ["sb-item"]
    assert _classes(right) == ["sb-item", "sb-right"]


@pytest.mark.parametrize("tone", ui.TONES)
def test_verdict_classes_follow_the_tone(tone):
    _, class_name = ui.verdict_children("X", tone)
    assert class_name == f"verdict verdict--{tone}"


def test_a_stale_verdict_says_so_in_its_own_cell():
    children, class_name = ui.verdict_children("PASS", "pass", [ui.Cell("Margin", "+0.4", tone="good")], stale=True)
    assert class_name.endswith("verdict--stale")
    assert "vd-stale" in _classes(children[1])
    assert children[2].children[1].className == "vd-val vd-val--good"


def test_a_not_run_verdict_has_no_stale_cell():
    children, _ = ui.verdict_children("NOT RUN", "none", stale=True)
    assert len(children) == 1


def test_bad_tones_are_refused():
    with pytest.raises(ValueError):
        ui.verdict_children("X", "green")
    with pytest.raises(ValueError):
        ui.verdict_children("X", "pass", [ui.Cell("a", "b", tone="amber")])


def test_busy_starts_hidden_with_its_variants():
    assert ui.busy("x", id="b").style == {"display": "none"}
    assert _classes(ui.busy("x", id="b", toast=True)) == ["busy", "busy-float", "busy-toast"]


def test_the_demo_app_builds():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "examples" / "dash_demo.py"
    spec = importlib.util.spec_from_file_location("dash_demo", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.app.server.test_client().get("/").status_code == 200
