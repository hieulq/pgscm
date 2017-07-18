from flask import Flask, request, g, url_for
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_potion import Api
from flask_security import Security, SQLAlchemyUserDatastore, \
    utils as security_utils
from flask_sqlalchemy import SQLAlchemy
from flask_security import user_registered
from flask_babelex import Babel
from adminlte import AdminLTE
from config import config
import uuid

from pgscm.security import forms

# Blueprint
from pgscm.admin import admin as admin_blueprint
from pgscm.certificate import certificate as certificate_blueprint
from pgscm.main import main as main_blueprint

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
sqla = SQLAlchemy()
babel = Babel()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'security.login'

from pgscm.db.models import User, Role  # noqa

user_datastore = SQLAlchemyUserDatastore(sqla, User, Role)
sec = Security()
api = Api()


def register_extensions(app):
    babel.init_app(app)
    bootstrap.init_app(app)
    AdminLTE(app)
    mail.init_app(app)
    moment.init_app(app)
    sqla.init_app(app)
    login_manager.init_app(app)

    # Init flask security using factory method, then change the localized
    # domain to our own
    sec_state = sec.init_app(app,
                             user_datastore, register_form=forms.RegisterForm)
    sec_state.i18n_domain.dirname = None

    # Flask potion do not initialize with current Flask app, so the below line
    # is the work-around for potion to init_app correctly.
    api.app = app
    api.init_app(app)


def register_api_resource(api):
    from pgscm.db import resources
    resources.init_resources(api)


def register_blueprint(app):
    app.register_blueprint(main_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(certificate_blueprint)


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprint(app)
    register_api_resource(api)

    # i18n locale selector
    @babel.localeselector
    def get_locale():
        lang = request.path[1:].split('/', 1)[0]
        if lang in config[config_name].MULTILANGUAGE_LANGS:
            return lang
        else:
            return 'vi'

    # Default role for new user is 'user'
    @user_registered.connect_via(app)
    def user_registered_sighandler(app, user, confirm_token):
        default_role = user_datastore.find_role('regional_user')
        user_datastore.add_role_to_user(user, default_role)
        sqla.session.commit()

    @app.context_processor
    def inject_custom():
        filters = {
            'lurl_for': lambda ep, **kwargs: url_for(ep + '_' + g.language,
                                                     **kwargs)
        }
        return filters

    @app.before_request
    def inject_global_proxy():
        # append babel i18n to flask global proxy object
        g.babel = babel
        g.language = get_locale()

    @app.before_first_request
    def create_user():
        # for master data in DB
        sqla.create_all()

        if not user_datastore.find_user(email='admin@pgs.com'):
            user_datastore.create_user(id=str(uuid.uuid4()),
                                       email='admin@pgs.com', fullname="Admin",
                                       password=security_utils.hash_password(
                                           'password'))
        if not user_datastore.find_user(email='mod@pgs.com'):
            user_datastore.create_user(id=str(uuid.uuid4()),
                                       email='mod@pgs.com', fullname="Mod",
                                       password=security_utils.hash_password(
                                           'password'))
        if not user_datastore.find_user(email='user@pgs.com'):
            user_datastore.create_user(id=str(uuid.uuid4()),
                                       email='user@pgs.com', fullname="User",
                                       password=security_utils.hash_password(
                                           'password'))
        # Commit any database changes; the User and Roles must exist
        # before we can add a Role to the User
        sqla.session.commit()

        user_datastore.add_role_to_user('admin@pgs.com', 'national_admin')
        user_datastore.add_role_to_user('mod@pgs.com', 'national_moderator')
        user_datastore.add_role_to_user('user@pgs.com', 'national_user')
        sqla.session.commit()

    return app
