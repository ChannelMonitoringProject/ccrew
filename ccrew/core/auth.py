from flask_security.models import fsqla_v3 as fsqla
from flask_security.utils import hash_password
from flask_security.core import Security
from ccrew.core import db
from ccrew.config import get_config


config = get_config()

fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):
    pass


class User(db.Model, fsqla.FsUserMixin):
    pass


def seed_auth(security: Security):
    user = config.ADMIN_USER
    password = config.ADMIN_PASSWORD
    if not security.datastore.find_user(email=user):
        if not user or not password:
            raise ValueError(
                "Missing user/password to seed, set environment ADMIN_USER and ADMIN_PASSWORD first"
            )
        admin_role = security.datastore.find_or_create_role(name="admin")
        admin_user = security.datastore.create_user(
            email=user, password=hash_password(password)
        )
        security.datastore.add_role_to_user(admin_user, admin_role)
        security.datastore.commit()
