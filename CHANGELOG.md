# Changelog

Versions follow semver. A **minor** release may add tokens, classes or helpers.
A **major** release renames or removes one, so apps on the old major keep their look until they choose to upgrade.

## 0.1.1 — 2026-11-14

- The package is typed: it ships a `py.typed` marker (PEP 561), so an app's mypy checks its calls into
  `app_ui_kit` instead of refusing the import (BeamAnalytiX runs mypy in CI). No CSS, JS or API change.

## 0.1.0 — 2026-11-14

First release, extracted from jointLab's workspace (which took its frame from BeamAnalytiX):

- `app-ui-kit.css`: design tokens, including:
  - the palette;
  - the engineering-paper ground;
  - the title-bar and status-bar tone;
  - Bootstrap 5 and Dash 4 variables.

  It also carries:
  - the page frame (`.app`, `.appbar`, `.workspace`, `.model`, `.main`, `.statusbar`);
  - numbered steps, the Run button and Auto-run, and the verdict bar;
  - the activity indicator (`.busy`);
  - tabs, cards, fields, buttons, results tables, status tags and alerts;
  - Dash dropdowns.
- `app-ui-kit.js`: light theme, Plotly recolouring from the tokens, one open step at a time, the Auto-run user gate (`window.appUiKit.userChangedRecently()`), and Plotly sizing in hidden tabs.
- `app_ui_kit.dash`: `use(app)` plus layout helpers. The helpers are `page`, `appbar`, `seg_toggle`, `model_pane`, `step`, `run_tools`, `results_column`, `statusbar`, `verdict_bar`, `verdict_children` and `busy`.
- `app_ui_kit.flask`: `init_app(app)` plus Jinja helpers for Python apps without Dash.
- `templates/shell.html`: the page skeleton for apps without Dash.

Renamed from jointLab's class names:

| jointLab | app-ui-kit |
|---|---|
| `.unit-toggle`, `.unit-toggle-label` | `.seg-toggle`, `.seg-toggle-label` |
| `.jl-spinner`, `.jl-spinner-bars`, `.jl-spinner-label` | `.busy`, `.busy-bars`, `.busy-label` |
| `.jl-toast` | `.busy-toast` |
| `.card-header-jl` | `.card-head` |
| `.geom-warning` | `.notice-warning` |
| `window.jointlabRunGate.userChangedRecently()` | `window.appUiKit.userChangedRecently()` |

`.ms-pass` / `.ms-fail` / `.ms-warn` are kept, alongside `.tag-pass` / `.tag-fail` / `.tag-warn`.
