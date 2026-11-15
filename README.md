# app-ui-kit

This is the shared look of every app in the family. Every app imports it; none copies it.

It is one CSS file and one JS file, plus thin helpers for Dash and Flask:

| File | What it holds |
|---|---|
| [`src/app_ui_kit/static/app-ui-kit.css`](src/app_ui_kit/static/app-ui-kit.css) | Design tokens; the engineering-paper page; the frame (title bar, left pane, results column, status bar); steps, Run and Auto-run; the verdict bar; tabs, cards, fields, buttons, tables, tags and alerts |
| [`src/app_ui_kit/static/app-ui-kit.js`](src/app_ui_kit/static/app-ui-kit.js) | Light theme; Plotly recolouring; one open step at a time; the Auto-run gate; Plotly sizing in hidden tabs |
| [`src/app_ui_kit/dash.py`](src/app_ui_kit/dash.py) | `use(app)` and layout helpers that build the frame |
| [`src/app_ui_kit/flask.py`](src/app_ui_kit/flask.py) | Serves the two files from any Flask app |
| [`templates/shell.html`](templates/shell.html) | The page skeleton (class names) for apps without Dash |
| [`examples/dash_demo.py`](examples/dash_demo.py) | A working Dash app using every piece: start new apps from it |

```
+---------------------------------------------------------------+
| title bar: wordmark · case line                        tools  |
+--------------------+------------------------------------------+
| Model  [ ]Auto-run [▶ Run] | verdict bar  PASS | Margin +0.42 |
| 1 Geometry   2 × 4 in   >  | Results | ...          Methods   |
| 2 Loads                 v  |   (results on engineering paper) |
|   (the open step's inputs) |                                  |
+--------------------+------------------------------------------+
| status bar                                                    |
+---------------------------------------------------------------+
```

## Rules

1. **Import, never copy.** The kit is a baseline: an app restyles or adds effects in its own CSS, which loads after the kit. Override a **token** (`:root { --model-w: 360px; }`) or restyle a component; never paste the kit's files into the app.
2. **Pin a version.** Apps install a tag (e.g. `v0.1.1`), never `main`. That way a kit change reaches an app only when that app upgrades.
3. **Change the look here, once.** Do it in a new version, with a `CHANGELOG.md` entry. Renaming or removing a class or token is a major version.

## Installing

The repo is public, so nothing needs a token: not your machine, Render, CI or a browser. Always install a tag (below, `v0.1.1`; see `CHANGELOG.md` for the latest).

### Dash apps

In `requirements.txt` (or `pyproject.toml`):

```
app-ui-kit[dash] @ git+https://github.com/CentrixCoder/app-ui-kit.git@v0.1.1
```

> **Hash-locked apps (`pip install --require-hashes`, like jointLab):** pip cannot hash a git requirement. Keep the kit out of the lock and install it in a second step:
>
> ```
> pip install --require-hashes -r requirements.lock && pip install --no-deps "app-ui-kit @ git+https://github.com/CentrixCoder/app-ui-kit.git@v0.1.1"
> ```

```python
import dash_bootstrap_components as dbc
from dash import Dash
from app_ui_kit import dash as ui

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
ui.use(app)          # serves /_app-ui-kit/<version>-<hash>/app-ui-kit.css and .js from the package

app.layout = ui.page(
    appbar=ui.appbar("beam", "AnalytiX"),
    model=ui.model_pane([ui.step(1, "Geometry", [...], step_id="geometry", open=True)], tools=ui.run_tools()),
    main=ui.results_column([ui.verdict_bar(), ...]),
    statusbar=ui.statusbar(["Not run", "beamAnalytiX · beam analysis"], right="An aid, not a sign-off"),
)
```

Run the demo:

```bash
pip install -e ".[dash]"
```

```bash
python examples/dash_demo.py
```

### Other Python apps (Flask)

```
app-ui-kit[flask] @ git+https://github.com/CentrixCoder/app-ui-kit.git@v0.1.1
```

```python
from app_ui_kit.flask import init_app
init_app(app)
```

In the template, put `{{ app_ui_kit_head() }}` in `<head>` (after Bootstrap, before your own CSS). Put `{{ app_ui_kit_scripts() }}` at the end of `<body>`. Copy the structure from `templates/shell.html`.

### npm apps (React, TypeScript, Vite, Next...)

In `package.json`:

```json
"dependencies": { "app-ui-kit": "github:CentrixCoder/app-ui-kit#v0.1.1" }
```

```js
import "app-ui-kit/app-ui-kit.css";   // once, in the entry file, before the app's own CSS
import "app-ui-kit/app-ui-kit.js";
```

Use the class names from `templates/shell.html` in your components.

### Plain HTML / static sites

Link the two files from the jsDelivr CDN, pinned to a tag (no build step, no copy):

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/CentrixCoder/app-ui-kit@v0.1.1/src/app_ui_kit/static/app-ui-kit.css">
<script src="https://cdn.jsdelivr.net/gh/CentrixCoder/app-ui-kit@v0.1.1/src/app_ui_kit/static/app-ui-kit.js"></script>
```

Put the `<link>` after Bootstrap (if used) and before your own CSS, and the `<script>` at the end of `<body>`. Copy the page structure from `templates/shell.html`.

## Developing the kit

```bash
pip install -e ".[test]"
```

```bash
pytest
```

The tests check the following:

- one version number across `__init__.py`, `package.json`, `app-ui-kit.js` and `CHANGELOG.md`;
- every `var(--token)` the CSS uses is defined;
- no app-specific names have crept into the shared files;
- the Dash and Flask wiring serves the files in the right order.

To release:

1. Bump `__version__`, `package.json` and the version in `app-ui-kit.js`.
2. Add a `CHANGELOG.md` entry.
3. Commit.
4. Tag `vX.Y.Z` and push the tag.
