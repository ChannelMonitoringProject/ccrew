from flask import Flask

from ccrew import ingestion
from ccrew import reporting

from ccrew.core import db, migrate
from ccrew.core.auth import User, Role, seed_auth
import ccrew.models
from ccrew.models.track import TrackedBoat
from flask_security.core import Security
from flask_security.datastore import SQLAlchemyUserDatastore
from flask_security.decorators import auth_required
from flask_security.models import fsqla_v3 as fsqla
from ccrew.config import get_config


def create_app(config=get_config()):
    app = Flask(__name__)
    app.config.from_object(get_config())
    db.init_app(app)
    migrate.init_app(app, db)

    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    # admin = Admin(app, name="ccrew")
    # admin.add_view(ModelView(TrackedBoat, db.session))

    # TODO change to factory pattern ( def create_bp() )
    ingestion_bp = ingestion.ingestion_bp
    app.register_blueprint(ingestion_bp)

    reporting_bp = reporting.bp
    app.register_blueprint(reporting_bp)

    # admin_bp = create_admin_blueprint()
    # app.register_blueprint(admin_bp)

    @app.route("/")
    def home():
        return {"message": "all good"}

    # TODO need to figure out how to make this work with flask_security
    # in order to restrict access to dashboard
    # At the moment this is public
    # reporting_dash_app = reporting.create_dash_app(app)

    # @app.route("/dashboard/")
    # @auth_required()
    # def reporting_dash_app():
    #     # reporting_dash_app = reporting.create_dash_app(app)
    #     dash_app = reporting.create_dash_app(app)
    #     app.register_blueprint(dash_app)

    with app.app_context():
        db.create_all()
        seed_auth(security)
        db.session.commit()

    return app
