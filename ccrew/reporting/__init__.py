import json
from flask_security.decorators import roles_required, auth_required

# from ccrew.reporting.dashboard import create_dash_app
import plotly
from ccrew.reporting import plotting
from flask import Blueprint, Response, jsonify

bp = Blueprint("reporting", __name__)


@bp.route("/api/reporting/tail")
@auth_required()
def tail() -> Response:
    fig = plotting.get_map_at()
    ret = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return Response(ret, mimetype="application/json")
