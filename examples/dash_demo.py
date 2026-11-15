"""
A runnable Dash app that uses every part of app-ui-kit: the reference for new apps.

    pip install -e ".[dash]"
    python examples/dash_demo.py        # http://127.0.0.1:8060
"""

from __future__ import annotations

import os

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html

from app_ui_kit import dash as ui

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title="appName")
ui.use(app)


def field(label, id, value):
    """A labelled number field. dbc.Input (a plain <input class="form-control">), as jointLab uses."""
    return html.Div(className="mb-2", children=[
        html.Label(label, className="input-label", htmlFor=id),
        dbc.Input(id=id, type="number", value=value, debounce=True),
    ])


def dash_field(label, id, value):
    """The same with Dash's own dcc.Input (a container with steppers): the kit styles both alike."""
    return html.Div(className="mb-2", children=[
        html.Label(label, className="input-label", htmlFor=id),
        dcc.Input(id=id, type="number", value=value, debounce=True),
    ])


app.layout = ui.page(
    appbar=ui.appbar("app", "Name", tools=ui.seg_toggle("Imperial · in, lbf", "Metric · mm, N", id="units")),
    model=ui.model_pane([
        ui.step(1, "Geometry", dbc.Card(dbc.CardBody([
            html.Div("Section", className="card-head"),
            field("Width, in", "in-w", 2.0),
            field("Depth, in", "in-d", 4.0),
            html.P("Inputs stay mounted while their step is closed.", className="field-helper"),
        ])), step_id="geometry", open=True),
        ui.step(2, "Loads", dbc.Card(dbc.CardBody([
            html.Div("Applied", className="card-head"),
            dash_field("Moment, in-lbf", "in-m", 12000),
        ])), step_id="loads"),
        ui.step(3, "Material", dbc.Card(dbc.CardBody([
            html.Div("Allowable", className="card-head"),
            field("Allowable stress, psi", "in-f", 40000),
        ])), step_id="material"),
    ], tools=ui.run_tools(run_id="btn-run")),
    main=ui.results_column([
        ui.verdict_bar(),
        html.Div(className="run-feedback", children=[
            ui.busy("Analyzing…", id="busy-run", floating=True),
            html.Div(id="run-status"),
        ]),
        dbc.Tabs(className="results-tabs", active_tab="tab-results", children=[
            dbc.Tab(label="Results", tab_id="tab-results", children=[
                dbc.Card(dbc.CardBody([
                    html.Div("Stress", className="card-head"),
                    html.Div(id="results-table"),
                ]), className="mb-2"),
                dbc.Card(dbc.CardBody([
                    html.Div("Utilisation", className="card-head"),
                    dcc.Graph(id="fig", config={"displayModeBar": False}, style={"height": "260px"}),
                ])),
            ]),
            dbc.Tab(label="Methods", tab_id="tab-methods", tab_class_name="tab-ref", children=[
                dbc.Card(dbc.CardBody([html.Div("Method", className="card-head"),
                                       html.P("σ = M·c / I, with c = d/2 and I = b·d³/12.")])),
            ]),
        ]),
    ]),
    statusbar=ui.statusbar(["Not run", "appName · app-ui-kit demo"], right="An aid, not a sign-off"),
)


@app.callback(
    Output("verdict", "children"), Output("verdict", "className"),
    Output("results-table", "children"), Output("fig", "figure"), Output("sb-run", "children"),
    Output("step-sum-geometry", "children"),
    Input("btn-run", "n_clicks"),
    State("in-w", "value"), State("in-d", "value"), State("in-m", "value"), State("in-f", "value"),
    running=[(Output("busy-run", "style"), {"display": "flex"}, {"display": "none"})],
)
def run(_clicks, b, d, m, f):
    b, d, m, f = (float(v or 0) for v in (b, d, m, f))
    stress = m * (d / 2) / (b * d ** 3 / 12) if b > 0 and d > 0 else float("inf")
    margin = f / stress - 1 if stress else float("inf")
    tone = "pass" if margin >= 0.1 else "warn" if margin >= 0 else "fail"
    children, class_name = ui.verdict_children(tone.upper(), tone, [
        ui.Cell("Governing", "Bending", wide=True),
        ui.Cell("Stress, psi", f"{stress:,.0f}"),
        ui.Cell("Margin", f"{margin:+.2f}", tone="good" if margin >= 0 else "bad"),
    ])
    tag = "tag-pass" if margin >= 0.1 else "tag-warn" if margin >= 0 else "tag-fail"
    table = html.Table(className="results-table w-100", children=[
        html.Thead(html.Tr([html.Th("Mode"), html.Th("Stress, psi"), html.Th("Margin")])),
        html.Tbody(html.Tr([html.Td("Bending"), html.Td(f"{stress:,.0f}"),
                            html.Td(html.Span(f"{margin:+.2f}", className=tag))])),
    ])
    figure = go.Figure(go.Bar(x=["Bending"], y=[stress / f if f else 0], marker_color="#1f5fbf"))
    figure.update_layout(margin=dict(l=40, r=10, t=10, b=30), yaxis_title="Stress / allowable")
    return children, class_name, table, figure, "Run complete", f"{b:g} × {d:g} in"


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", "8060")))
