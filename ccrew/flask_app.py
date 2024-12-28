from flask import Flask
from ccrew import ingestion
from ccrew import ingestion
from ccrew import reporting
from ccrew.core import db, migrate
import ccrew.models

from ccrew.config import get_config


def create_app(config=get_config()):
    app = Flask(__name__)
    app.config.from_object(get_config())
    db.init_app(app)
    migrate.init_app(app, db)

    # TODO change to factory pattern ( def create_bp() )
    ingestion_bp = ingestion.ingestion_bp
    app.register_blueprint(ingestion_bp)

    reporting_dash_app = reporting.create_dash_app(app)

    with app.app_context():
        db.create_all()

    return app
