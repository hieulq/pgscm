from flask import Blueprint

farmer = Blueprint('farmer', __name__)

from pgscm.farmer import views  # noqa
