from flask import Blueprint

certificate = Blueprint('certificate', __name__)

from pgscm.certificate import views  # noqa
