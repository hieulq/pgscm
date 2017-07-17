import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # common
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    # mail config options
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    NAME = 'PGS Certificate Management'
    MAIL_USE_TLS = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    PGS_MAIL_SUBJECT_PREFIX = '[PGS Cert Mgr]'
    PGS_MAIL_SENDER = 'PGS Admin <pgs@example.com>'
    PGS_ADMIN = os.environ.get('PGS_ADMIN')

    # i18n
    BABEL_DEFAULT_LOCALE = 'vi'
    BABEL_DEFAULT_TIMEZONE = 'ICT'

    # security
    SECURITY_PASSWORD_SALT = 'PGS'
    SECURITY_TRACKABLE = True
    SECURITY_REGISTERABLE = True
    SECURITY_URL_PREFIX = '/auth'
    SECURITY_SEND_REGISTER_EMAIL = False

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
    #     'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    SQLALCHEMY_DATABASE_URI = \
        'mysql+pymysql://root:pgscm@localhost:3306/pgscm'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
