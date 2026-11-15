"""
app_ui_kit.dash: the shared page frame for Dash apps.

    import dash_bootstrap_components as dbc
    from dash import Dash, html
    from app_ui_kit import dash as ui

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    ui.use(app)                                   # the kit's CSS and JS, served from this package

    app.layout = ui.page(
        appbar=ui.appbar("beam", "AnalytiX"),
        model=ui.model_pane([
            ui.step(1, "Geometry", [...], step_id="geometry", open=True),
            ui.step(2, "Loads", [...], step_id="loads"),
        ], tools=ui.run_tools()),
        main=ui.results_column([ui.verdict_bar(), dbc.Tabs([...], className="results-tabs")]),
        statusbar=ui.statusbar(["Not run", "beamAnalytiX · beam analysis"], right="An aid, not a sign-off"),
    )

    +---------------------------------------------------------------+
    | appbar: wordmark · case line                          tools   |
    +--------------------+------------------------------------------+
    | model pane          | main: verdict bar, feedback, tabs       |
    |  1 step  summary >  |                                          |
    |  2 step  summary v  |                                          |
    +--------------------+------------------------------------------+
    | statusbar                                                     |
    +---------------------------------------------------------------+

Layout only: no callbacks. Every step stays MOUNTED whether open or not
(html.Details only hides its body), so a Run callback can read State from
every input. Keep it that way: do not swap a step's body for content created
on demand.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Union

from dash import html

from app_ui_kit import SCRIPT, STYLESHEET, versioned_url
from app_ui_kit.flask import init_app as _init_flask

Children = Union[None, str, object, Sequence[object]]

TONES = ("none", "pass", "warn", "fail")


# ---------------------------------------------------------------- wiring
def use(app) -> None:
    """Serve the kit's CSS and JS from this package and add them to ``app``'s page.

    The stylesheet goes after the ``external_stylesheets`` already given (so
    after Bootstrap) and before the app's own ``assets/`` CSS, which can
    therefore override any token. Call once, before the app serves a page.
    """
    _init_flask(app.server, prefix=app.config.routes_pathname_prefix)
    href = versioned_url(STYLESHEET, app.config.requests_pathname_prefix)
    src = versioned_url(SCRIPT, app.config.requests_pathname_prefix)
    sheets = list(app.config.external_stylesheets or [])
    if href not in sheets:
        app.config.external_stylesheets = [*sheets, href]
    scripts = list(app.config.external_scripts or [])
    if src not in scripts:
        app.config.external_scripts = [*scripts, src]


# ---------------------------------------------------------------- the frame
def page(appbar, main, statusbar, model=None, extra: Iterable[object] = ()) -> html.Div:
    """The whole page: title bar, workspace (left pane + results column), status bar.

    ``extra`` holds anything that is not drawn (dcc.Store, dcc.Location...).
    With no ``model`` the results column takes the full width.
    """
    workspace_class = "workspace" if model is not None else "workspace workspace--single"
    panes = [model, main] if model is not None else [main]
    return html.Div(className="app", children=[
        *extra,
        appbar,
        html.Div(className=workspace_class, children=panes),
        statusbar,
    ])


def appbar(name_a: str, name_b: str = "", *, case_id: Optional[str] = "app-case",
           tools: Children = None) -> html.Header:
    """The title bar: a two-tone italic wordmark (``name_a`` dark, ``name_b`` accent),
    a case line (``case_id``, filled by the app's callbacks) and tools at the right."""
    brand = [html.H1(className="wordmark", title=f"{name_a}{name_b}", children=[
        html.Span(name_a, className="wm-a"), html.Span(name_b, className="wm-b"),
    ])]
    if case_id:
        brand.append(html.P(id=case_id, className="case"))
    return html.Header(className="appbar", children=[
        html.Div(className="brand", children=brand),
        html.Div(className="appbar-tools", children=_as_list(tools)),
    ])


def seg_toggle(first: str, second: str, *, id: str, pressed: bool = False,
               title: Optional[str] = None) -> html.Button:
    """A two-way switch drawn as one segmented control (e.g. display units).

    ``pressed=False`` lights ``first``; a callback flips ``aria-pressed`` on click.
    """
    return html.Button(
        [html.Span(first, className="seg-toggle-label"), html.Span(second, className="seg-toggle-label")],
        id=id, n_clicks=0, type="button", className="seg-toggle", title=title,
        **{"aria-label": title or f"{first} / {second}", "aria-pressed": "true" if pressed else "false"},
    )


def model_pane(steps: Sequence[object], *, title: str = "Model", tools: Children = None,
               id: Optional[str] = None) -> html.Aside:
    """The left pane: a sticky heading with ``tools`` (e.g. ``run_tools()``), then the steps.

    Sets ``--model-steps`` so the open step's inputs scroll inside the pane
    while every step heading stays in view.
    """
    kwargs = {"id": id} if id else {}
    return html.Aside(className="model", style={"--model-steps": str(len(steps))}, children=[
        html.Div(className="pane-head", children=[
            html.H2(title),
            html.Div(className="run-tools", children=_as_list(tools)),
        ]),
        *steps,
    ], **kwargs)


def step(number: int, title: str, children: Children, *, step_id: str, open: bool = False,
         summary_id: Optional[str] = None) -> html.Details:
    """One numbered step of the left pane: heading, a one-line summary, the inputs.

    The summary span's id defaults to ``step-sum-<step_id>`` for a callback to fill.
    The kit's JS keeps one step open at a time.
    """
    return html.Details(id=f"step-{step_id}", className="step", open=open, children=[
        html.Summary(className="step-head", children=[
            html.Span(str(number), className="step-num"),
            html.Span(title, className="step-title"),
            html.Span(id=summary_id or f"step-sum-{step_id}", className="step-sum"),
        ]),
        html.Div(className="step-body", children=children),
    ])


def run_tools(*, run_id: str = "btn-run", auto_run_id: Optional[str] = "chk-auto-run",
              label: str = "Run analysis", title: Optional[str] = None) -> list:
    """The Run button, with an Auto-run checkbox (remembered in this browser).

    Gate an Auto-run callback on ``window.appUiKit.userChangedRecently()`` so values
    set by callbacks (page load, restored state) do not trigger a run.
    Needs dash-bootstrap-components for the checkbox (``pip install app-ui-kit[dash]``).
    """
    button = html.Button(
        [html.Span("▶", className="run-glyph", **{"aria-hidden": "true"}), label],
        id=run_id, n_clicks=0, type="button", className="btn run-btn", title=title or label,
    )
    if not auto_run_id:
        return [button]
    import dash_bootstrap_components as dbc

    checkbox = dbc.Checklist(
        id=auto_run_id, value=[], persistence=True, persistence_type="local", className="auto-run",
        options=[{"label": "Auto-run", "value": "auto"}],
    )
    return [checkbox, button]


def results_column(children: Children, *, id: str = "results-column") -> html.Main:
    """The right column on engineering paper: verdict bar, run feedback, tabs."""
    return html.Main(id=id, className="main", children=_as_list(children))


def statusbar(items: Sequence[Children], *, right: Children = None, first_id: Optional[str] = "sb-run") -> html.Footer:
    """The status bar: items from the left, ``right`` pinned at the right.

    The first item gets ``first_id`` (default ``sb-run``) for a callback to update.
    """
    spans = []
    for index, item in enumerate(items):
        kwargs = {"id": first_id} if index == 0 and first_id else {}
        spans.append(html.Span(item, className="sb-item", **kwargs))
    if right is not None:
        spans.append(html.Span(right, className="sb-item sb-right"))
    return html.Footer(className="statusbar", children=spans)


# ---------------------------------------------------------------- the verdict bar
@dataclass(frozen=True)
class Cell:
    """One caption/value pair in the verdict bar. ``tone``: None, "good" or "bad"."""
    caption: str
    value: Children
    tone: Optional[str] = None
    wide: bool = False


def verdict_children(status: str, tone: str = "none", cells: Sequence[Cell] = (), *,
                     stale: bool = False, stale_text: str = "Out of date") -> tuple[list, str]:
    """``(children, className)`` of the verdict bar, for a callback to return.

    ``tone`` is one of ``"none" | "pass" | "warn" | "fail"``. ``stale=True`` marks
    results kept from earlier inputs: the status fades and an amber cell says so.
    """
    if tone not in TONES:
        raise ValueError(f"tone must be one of {TONES}, not {tone!r}")
    children = [html.Span(status, className="vd-status")]
    if stale and tone != "none":
        children.append(html.Div(className="vd-cell vd-stale", children=[
            html.Span("Results", className="vd-cap"), html.Span(stale_text, className="vd-val"),
        ]))
    for cell in cells:
        if cell.tone not in (None, "good", "bad"):
            raise ValueError(f"cell tone must be None, 'good' or 'bad', not {cell.tone!r}")
        children.append(html.Div(className="vd-cell" + (" vd-wide" if cell.wide else ""), children=[
            html.Span(cell.caption, className="vd-cap"),
            html.Span(cell.value, className="vd-val" + (f" vd-val--{cell.tone}" if cell.tone else ""),
                      title=cell.value if isinstance(cell.value, str) else None),
        ]))
    return children, f"verdict verdict--{tone}" + (" verdict--stale" if stale else "")


def verdict_bar(status: str = "NOT RUN", tone: str = "none", cells: Sequence[Cell] = (), *,
                stale: bool = False, id: str = "verdict") -> html.Div:
    """The verdict bar, sticky at the top of the results column."""
    children, class_name = verdict_children(status, tone, cells, stale=stale)
    return html.Div(id=id, className=class_name, role="status", children=children)


# ---------------------------------------------------------------- activity indicator
def busy(label: str, *, id: str, floating: bool = False, toast: bool = False) -> html.Div:
    """An activity indicator (equaliser bars), hidden until shown.

    Show it for exactly as long as the work runs with the callback's
    ``running=[(Output(id, "style"), {"display": "flex"}, {"display": "none"})]``.
    ``floating`` pins it at the top centre of the window; ``toast`` makes it amber
    and prominent, for work the user is not watching.
    """
    class_name = "busy" + (" busy-float" if floating or toast else "") + (" busy-toast" if toast else "")
    return html.Div([html.Span(className="busy-bars"), html.Span(label, className="busy-label")],
                    id=id, className=class_name, style={"display": "none"})


def _as_list(children: Children) -> list:
    if children is None:
        return []
    if isinstance(children, (list, tuple)):
        return list(children)
    return [children]


__all__ = ["use", "page", "appbar", "seg_toggle", "model_pane", "step", "run_tools", "results_column",
           "statusbar", "Cell", "verdict_children", "verdict_bar", "busy", "TONES"]
