from flask import Blueprint
from flask_security import auth_required, roles_required
from flask_security.decorators import roles_required


def create_admin_blueprint():
    admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

    @admin_bp.route("/")
    @auth_required()
    @roles_required("admin")
    def admin_root():
        return {"message": "admin root"}

    @admin_bp.route("/users")
    @auth_required()
    @roles_required("admin")
    def users():
        pass

    return admin_bp
