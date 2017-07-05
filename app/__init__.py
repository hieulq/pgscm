from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_potion import Api
from flask_security import Security, SQLAlchemyUserDatastore, utils
from flask_sqlalchemy import SQLAlchemy

from adminlte import AdminLTE
from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
sqla = SQLAlchemy()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

from app.db.models import User, Role
user_datastore = SQLAlchemyUserDatastore(sqla, User, Role)
security = Security()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    api = Api(app)
    bootstrap.init_app(app)
    AdminLTE(app)
    mail.init_app(app)
    moment.init_app(app)
    sqla.init_app(app)
    login_manager.init_app(app)
    security.init_app(app, user_datastore)

    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from app.db import resources
    resources.init_resources(api)

    @app.before_first_request
    def create_user():
        sqla.create_all()
        # Create the Roles "admin" and "end-user" -- unless they already exist
        user_datastore.find_or_create_role(name='admin',
                                           description='Administrator')
        user_datastore.find_or_create_role(name='mod',
                                           description='Moderator')
        user_datastore.find_or_create_role(name='user',
                                           description='Normal User')

        if not user_datastore.find_user(username='admin'):
            user_datastore.create_user(username='admin', email='admin@pgs.com',
                                       password=utils.hash_password('password'))
        if not user_datastore.find_user(username='mod'):
            user_datastore.create_user(username='mod', email='mod@pgs.com',
                                       password=utils.hash_password('password'))
        if not user_datastore.find_user(username='user'):
            user_datastore.create_user(username='user', email='user@pgs.com',
                                       password=utils.hash_password('password'))
        # Commit any database changes; the User and Roles must exist
        # before we can add a Role to the User
        sqla.session.commit()

        user_datastore.add_role_to_user('admin@pgs.com', 'admin')
        user_datastore.add_role_to_user('mod@pgs.com', 'mod')
        user_datastore.add_role_to_user('user@pgs.com', 'user')
        sqla.session.commit()

    return app
