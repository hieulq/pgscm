from flask import Blueprint

group = Blueprint('group', __name__)

from pgscm.group import views  # noqa
