from flask import Blueprint

report = Blueprint('report', __name__)

from pgscm.report import views  # noqa
