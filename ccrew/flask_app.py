from flask import Flask
from ccrew import ingestion
from ccrew.ingestion import ingestion_bp
from ccrew.core import db, migrate, celery
import ccrew.models

from ccrew.config import get_config


def create_app(config=get_config()):
    app = Flask(__name__)
    app.config.from_object(get_config())
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(ingestion_bp)
    with app.app_context():
        db.create_all()

    return app
