from flask import Flask
from ccrew import ingestion
from ccrew import ingestion
from ccrew import reporting
from ccrew.core import db, migrate
import ccrew.models
from flask_security import (
    Security,
    SQLAlchemyUserDatastore,
    auth_required,
    hash_password,
)
from flask_security.models import fsqla_v3 as fsqla

from ccrew.config import get_config


def create_app(config=get_config()):
    app = Flask(__name__)
    app.config.from_object(get_config())
    db.init_app(app)
    migrate.init_app(app, db)

    fsqla.FsModels.set_db_info(db)

    class Role(db.Model, fsqla.FsRoleMixin):
        pass

    class User(db.Model, fsqla.FsUserMixin):
        pass

    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    @app.route("/")
    @auth_required()
    def home():
        return {"message": "all good"}

    # TODO change to factory pattern ( def create_bp() )
    ingestion_bp = ingestion.ingestion_bp
    app.register_blueprint(ingestion_bp)

    reporting_dash_app = reporting.create_dash_app(app)

    with app.app_context():
        db.create_all()
        if not security.datastore.find_user(email="test@me.com"):
            security.datastore.create_user(
                email="test@me.com", password=hash_password("password")
            )
        db.session.commit()

    return app
