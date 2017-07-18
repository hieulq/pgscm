from flask import Blueprint

admin = Blueprint('admin', __name__)

from pgscm.admin import views  # noqa
