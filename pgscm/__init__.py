from flask import Flask, request, g, url_for
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_required
from flask_mail import Mail
from flask_potion import Api
from flask_potion.contrib.principals import principals
from flask_security import Security, SQLAlchemyUserDatastore, \
    utils as security_utils
from flask_sqlalchemy import SQLAlchemy
from flask_security import user_registered
from flask_babelex import Babel

from adminlte import AdminLTE
from config import config
import uuid

from pgscm import const
from pgscm.utils import PgsPotionManager


bootstrap = Bootstrap()
mail = Mail()
sqla = SQLAlchemy()
babel = Babel()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'security.login'

from pgscm.db.models import User, Role  # noqa

user_datastore = SQLAlchemyUserDatastore(sqla, User, Role)
sec = Security()
api = Api()


def register_security(app):
    # Init flask security using factory method, then change the localized
    # domain to our own
    from pgscm.security import forms
    sec_state = sec.init_app(app, user_datastore,
                             register_form=forms.RegisterForm,
                             login_form=forms.LoginForm)
    sec_state.i18n_domain.dirname = None


def register_extensions(app):
    babel.init_app(app)
    bootstrap.init_app(app)
    AdminLTE(app)
    mail.init_app(app)
    sqla.init_app(app)
    login_manager.init_app(app)

    # Flask potion do not initialize with current Flask app, so the below line
    # is the work-around for potion to init_app correctly.
    api.app = app
    api.decorators = [login_required]
    api.default_manager = principals(PgsPotionManager)
    api.init_app(app)


def register_api_resource(api_mgr):
    from pgscm.db import resources
    resources.init_resources(api_mgr)


def register_blueprint(app):
    # Blueprint
    from pgscm.admin import admin as admin_blueprint
    from pgscm.certificate import certificate as certificate_blueprint
    from pgscm.main import main as main_blueprint
    from pgscm.group import group as group_blueprint
    from pgscm.farmer import farmer as farmer_blueprint
    from pgscm.associate_group import agroup as agroup_blueprint
    from pgscm.report import report as report_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(certificate_blueprint)
    app.register_blueprint(group_blueprint)
    app.register_blueprint(agroup_blueprint)
    app.register_blueprint(farmer_blueprint)
    app.register_blueprint(report_blueprint)


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprint(app)
    register_api_resource(api)
    register_security(app)

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
        g.c = const

    @app.before_first_request
    def create_user():
        # for master data in DB
        sqla.create_all()

        if not user_datastore.find_role(const.C_USER):
            user_datastore.create_role(id=str(uuid.uuid4()),
                                       name=const.C_USER,
                                       description='Customer Role')

        if not user_datastore.find_user(email='admin@pgs.com'):
            user_datastore.create_user(id=str(uuid.uuid4()),
                                       email='admin@pgs.com', fullname="Admin",
                                       password=security_utils.hash_password(
                                           'password'))
        if not user_datastore.find_user(email='radmin@pgs.com'):
            user_datastore.create_user(id=str(uuid.uuid4()),
                                       email='radmin@pgs.com',
                                       fullname="Regional Admin",
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

        user_datastore.add_role_to_user('admin@pgs.com', const.N_ADMIN)
        user_datastore.add_role_to_user('radmin@pgs.com', const.R_ADMIN)
        user_datastore.add_role_to_user('mod@pgs.com', const.N_MOD)
        user_datastore.add_role_to_user('user@pgs.com', const.N_USER)
        sqla.session.commit()

    return app
