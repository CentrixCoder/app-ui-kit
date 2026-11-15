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

1. **Import, never copy.** If an app needs a different look, override a **token** in the app's own CSS. That CSS loads after the kit. For example, `:root { --model-w: 360px; }`.
2. **Pin a version.** Apps install a tag (`v0.1.0`), never `main`. That way a kit change reaches an app only when that app upgrades.
3. **Change the look here, once.** Do it in a new version, with a `CHANGELOG.md` entry. Renaming or removing a class or token is a major version.

## Installing (private repo)

The repo is private, so installing needs GitHub credentials.

- **On your own machine:** your normal git login is enough.
- **On Render (or any CI):** the build needs a token.
  1. On GitHub, create a fine-grained personal access token with **read-only Contents** access to **this one repository**.
  2. In each Render service, under **Environment**, add it as `GITHUB_TOKEN`.
  3. Put this line at the start of the service's build command:

     ```bash
     git config --global url."https://x-access-token:${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/" &&
     ```

  It lets both `pip` and `npm` fetch the repo, and keeps the token out of every file in the app.

### Dash apps

In `requirements.txt` (or `pyproject.toml`):

```
app-ui-kit[dash] @ git+https://github.com/CentrixCoder/app-ui-kit.git@v0.1.0
```

> **Hash-locked apps (`pip install --require-hashes`, like jointLab):** pip cannot hash a git requirement. Keep the kit out of the lock and install it in a second step:
>
> ```
> pip install --require-hashes -r requirements.lock && pip install --no-deps "app-ui-kit @ git+https://github.com/CentrixCoder/app-ui-kit.git@v0.1.0"
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
app-ui-kit[flask] @ git+https://github.com/CentrixCoder/app-ui-kit.git@v0.1.0
```

```python
from app_ui_kit.flask import init_app
init_app(app)
```

In the template, put `{{ app_ui_kit_head() }}` in `<head>` (after Bootstrap, before your own CSS). Put `{{ app_ui_kit_scripts() }}` at the end of `<body>`. Copy the structure from `templates/shell.html`.

### npm apps (React, TypeScript, Vite, Next...)

In `package.json`:

```json
"dependencies": { "app-ui-kit": "github:CentrixCoder/app-ui-kit#v0.1.0" }
```

```js
import "app-ui-kit/app-ui-kit.css";   // once, in the entry file, before the app's own CSS
import "app-ui-kit/app-ui-kit.js";
```

Use the class names from `templates/shell.html` in your components.

### Plain HTML / static sites

A browser cannot load files straight from a private repo. Add a build step that installs the kit with npm (above), then copy `node_modules/app-ui-kit/src/app_ui_kit/static/*` next to the page. Link them as `templates/shell.html` does.

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
