"""The package itself: one version, one copy of each file, no undefined tokens."""

from __future__ import annotations

import json
import re
from pathlib import Path

import app_ui_kit

ROOT = Path(__file__).resolve().parent.parent
CSS = app_ui_kit.static_path(app_ui_kit.STYLESHEET).read_text(encoding="utf-8")
JS = app_ui_kit.static_path(app_ui_kit.SCRIPT).read_text(encoding="utf-8")


def test_the_shipped_files_exist_and_are_not_empty():
    for name in (app_ui_kit.STYLESHEET, app_ui_kit.SCRIPT):
        path = app_ui_kit.static_path(name)
        assert path.is_file() and path.stat().st_size > 1000, path


def test_package_json_carries_the_python_version():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert package["version"] == app_ui_kit.__version__


def test_the_script_reports_the_python_version():
    assert f'version: "{app_ui_kit.__version__}"' in JS


def test_the_changelog_has_an_entry_for_this_version():
    assert f"## {app_ui_kit.__version__}" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_npm_exports_point_at_the_one_copy():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    for target in package["exports"].values():
        assert (ROOT / target).is_file(), target


def test_every_token_used_is_defined():
    """A var(--x) with no definition silently falls back (jointLab shipped two such)."""
    defined = set(re.findall(r"(--[\w-]+)\s*:", CSS))
    used = set(re.findall(r"var\(\s*(--[\w-]+)", CSS))
    # Bootstrap and Dash define their own; the kit only reads them where it sets them too
    missing = {name for name in used - defined if not name.startswith(("--bs-", "--Dash-"))}
    assert not missing, sorted(missing)


def test_the_css_braces_balance():
    without_comments = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
    assert without_comments.count("{") == without_comments.count("}")


def test_no_app_specific_names_leak_into_the_shared_files():
    shared = CSS + JS + (ROOT / "templates" / "shell.html").read_text(encoding="utf-8")
    body = re.sub(r"/\*.*?\*/", "", shared, flags=re.S)  # the header comments may name the source app
    for word in ("jointlab", "jointLab", "lug-", "bj-", "jl-"):
        assert word not in body, word


def test_versioned_url_rejects_unknown_files():
    import pytest

    with pytest.raises(ValueError):
        app_ui_kit.versioned_url("secrets.txt")
    url = app_ui_kit.versioned_url("app-ui-kit.css")
    assert re.fullmatch(rf"/_app-ui-kit/{re.escape(app_ui_kit.__version__)}-[0-9a-f]{{10}}/app-ui-kit\.css", url), url


def test_the_fingerprint_follows_the_file_content(monkeypatch, tmp_path):
    for name in (app_ui_kit.STYLESHEET, app_ui_kit.SCRIPT):
        (tmp_path / name).write_text("a", encoding="utf-8")
    monkeypatch.setattr(app_ui_kit, "static_dir", lambda: tmp_path)
    app_ui_kit.fingerprint.cache_clear()
    before = app_ui_kit.fingerprint()
    (tmp_path / app_ui_kit.STYLESHEET).write_text("b", encoding="utf-8")
    app_ui_kit.fingerprint.cache_clear()
    after = app_ui_kit.fingerprint()
    monkeypatch.undo()
    app_ui_kit.fingerprint.cache_clear()
    assert before != after


def test_the_package_is_typed():
    """PEP 561: apps run mypy against their calls into the kit (BeamAnalytiX's CI does)."""
    assert (Path(app_ui_kit.__file__).parent / "py.typed").is_file()
