import json
from dash import Dash, Input, Output, State, callback, dcc, html
from ccrew.reporting import plotting
from flask_security import current_user
from flask import redirect, url_for


def create_dash_app(base_flask_app):
    dash_app = Dash(
        server=base_flask_app,
        routes_pathname_prefix="/dashboard/",
    )

    # @dash_app.server.before_request
    # def restricted():
    #     if not current_user.is_authenticated:
    #         return redirect(url_for("security.login"))

    dash_app.layout = html.Div(
        id="dash-container",
        children=[
            html.H1("Dashboard"),
            dcc.Graph(id="current_state", figure=plotting.plot_state()),
            #     dcc.Interval(id="interval_component", interval=10 * 1000),
        ],
    )

    # @callback(
    #     Output("current_state", "extendData"),
    #     [Input("interval_component", "n_intervals")],
    #     [State("current_state", "figure")],
    # )
    # def update_state(n, existing):
    #     print("=============existing=============")
    #     print(json.dumps(existing, indent=2))
    #     trace = plotting.get_state_trace()
    #     existing["data"][0] = trace
    #     return existing

    return dash_app.server
