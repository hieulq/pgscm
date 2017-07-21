from flask import Blueprint

agroup = Blueprint('agroup', __name__)

from pgscm.associate_group import views  # noqa
