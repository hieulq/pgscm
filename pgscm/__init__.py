from flask import Flask, request, session
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_potion import Api
from flask_security import Security, SQLAlchemyUserDatastore, utils
from flask_sqlalchemy import SQLAlchemy
from flask_security import user_registered
from flask_babelex import Babel, Domain

from adminlte import AdminLTE
from config import config

from pgscm.security import forms

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
sqla = SQLAlchemy()
babel = Babel()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'security.login'

from pgscm.db.models import User, Role
user_datastore = SQLAlchemyUserDatastore(sqla, User, Role)
sec = Security()
api = Api()


@babel.localeselector
def get_locale():
    override = request.args.get('lang')
    if override:
        session['lang'] = override
    rv = session.get('lang', 'vi')
    return rv


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

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
    sec_dom = Domain()
    sec_state.i18n_domain.dirname = None

    # Flask potion do not initialize with current Flask app, so the below line
    # is the work-around for potion to init_app correctly.
    api.app = app
    api.init_app(app)

    from pgscm.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from pgscm.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from pgscm.db import resources
    resources.init_resources(api)

    # Default role for new user is 'user'
    @user_registered.connect_via(app)
    def user_registered_sighandler(app, user, confirm_token):
        default_role = user_datastore.find_role('user')
        user_datastore.add_role_to_user(user, default_role)
        sqla.session.commit()

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

        if not user_datastore.find_user(email='admin@pgs.com'):
            user_datastore.create_user(email='admin@pgs.com', fullname="Admin",
                                       password=utils.hash_password('password'))
        if not user_datastore.find_user(email='mod@pgs.com'):
            user_datastore.create_user(email='mod@pgs.com', fullname="Mod",
                                       password=utils.hash_password('password'))
        if not user_datastore.find_user(email='user@pgs.com'):
            user_datastore.create_user(email='user@pgs.com', fullname="User",
                                       password=utils.hash_password('password'))
        # Commit any database changes; the User and Roles must exist
        # before we can add a Role to the User
        sqla.session.commit()

        user_datastore.add_role_to_user('admin@pgs.com', 'admin')
        user_datastore.add_role_to_user('mod@pgs.com', 'mod')
        user_datastore.add_role_to_user('user@pgs.com', 'user')
        sqla.session.commit()

    return app
