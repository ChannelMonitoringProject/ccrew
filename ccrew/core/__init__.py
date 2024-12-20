from flask_sqlalchemy import SQLAlchemy
from ccrew.celery_app import create_celery_app
from flask_migrate import Migrate

# from . import db as db

db = SQLAlchemy()
migrate = Migrate()
celery = create_celery_app()
