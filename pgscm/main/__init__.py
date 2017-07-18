from flask import Blueprint

main = Blueprint('main', __name__)

from pgscm.main import views, errors  # noqa
