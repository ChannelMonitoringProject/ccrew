from flask import Flask
from ccrew import ingestion
from ccrew.ingestion import ingestion_bp

from ccrew.config import get_config


def create_app(config=get_config()):
    app = Flask(__name__)
    app.register_blueprint(ingestion_bp)
    return app
