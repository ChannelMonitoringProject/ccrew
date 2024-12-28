from dash import Dash, Input, Output, callback, dcc, html
from ccrew.reporting import plotting


def create_dash_app(base_flask_app):
    dash_app = Dash(
        server=base_flask_app,
        routes_pathname_prefix="/dashboard/",
    )
    dash_app.layout = html.Div(
        id="dash-container",
        children=[
            html.H1("Dashboard"),
            dcc.Graph(id="current_state", figure=plotting.plot_state()),
            #            dcc.Interval(id="interval_component", interval=10 * 1000),
        ],
    )

    # @callback(
    #     Output("current_state", "children"), Input("interval_component", "n_intervals")
    # )
    # def update_state(n):
    #     return plotting.plot_state()

    return dash_app.server
